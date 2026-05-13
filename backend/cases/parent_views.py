"""
Parent/child case endpoints (Tier 3 parent-child).

Three endpoints over and above what `CaseDetailView` already exposes:

* ``GET  /api/cases/<pk>/tree/``                   — descendant tree, max depth 3.
* ``POST /api/cases/<pk>/link/``                   — set/clear parent with explicit audit row.
* ``POST /api/cases/<pk>/close-with-children/``    — close parent and (optionally) cascade-close descendants.

The link endpoint takes a row lock on both rows so two concurrent agents cannot
build a cycle. Cascade close honours ``Org.auto_close_children_on_parent_close``
as the default, and accepts ``cascade`` in the body to override.
"""

from datetime import date

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Case
from common.models import Activity
from common.permissions import HasOrgContext


TREE_MAX_DEPTH = Case.PARENT_MAX_DEPTH


def _summary(case):
    """Lightweight node payload used by the tree response."""
    return {
        "id": str(case.id),
        "name": case.name,
        "status": case.status,
        "priority": case.priority,
        "is_problem": case.is_problem,
        "is_active": case.is_active,
        "assigned_to": [str(p.id) for p in case.assigned_to.all()],
    }


def _build_tree(case, depth=0):
    """Recurse to ``TREE_MAX_DEPTH``. Returns ``{...summary, children: [...]}``."""
    node = _summary(case)
    if depth >= TREE_MAX_DEPTH:
        node["children"] = []
        node["truncated"] = True
        return node
    children = list(case.children.all().prefetch_related("assigned_to"))
    node["children"] = [_build_tree(c, depth + 1) for c in children]
    return node


def _record(case, action, metadata, actor):
    Activity.objects.create(
        user=actor,
        action=action,
        entity_type="Case",
        entity_id=case.pk,
        entity_name=str(case)[:255],
        metadata=metadata,
        org_id=case.org_id,
    )


class CaseTreeView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request, pk):
        org = request.profile.org
        case = get_object_or_404(
            Case.objects.prefetch_related("assigned_to"), id=pk, org=org
        )
        # Return the root of the visible tree: walk up to the highest ancestor
        # in the same org so a child URL still shows the full incident.
        root = case
        seen = {root.id}
        while root.parent_id and root.parent and root.parent.org_id == org.id:
            if root.parent_id in seen:
                break
            seen.add(root.parent_id)
            root = root.parent
        return Response(
            {"root": _build_tree(root), "focus_id": str(case.id)},
            status=status.HTTP_200_OK,
        )


class CaseLinkParentView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        org = request.profile.org
        parent_id = request.data.get("parent_id")
        # Lock the case row so a parallel link from another agent cannot
        # race on the cycle check. We look up the parent under the same lock.
        case = (
            Case.objects.select_for_update()
            .filter(id=pk, org=org)
            .first()
        )
        if case is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        former_parent_id = case.parent_id

        if not parent_id:
            # Detach.
            if case.parent_id is None:
                return Response(
                    {"detail": "Case is not linked to a parent."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            case.parent = None
            case._parent_audit_skip = True
            case.save(update_fields=["parent"])
            _record(
                case,
                "UNLINKED_PARENT",
                {"former_parent_id": str(former_parent_id)},
                actor=request.profile,
            )
            return Response(
                {"id": str(case.id), "parent": None},
                status=status.HTTP_200_OK,
            )

        parent = (
            Case.objects.select_for_update()
            .filter(id=parent_id, org=org)
            .first()
        )
        if parent is None:
            return Response(
                {"parent_id": "Parent case not found in this organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if parent.id == case.id:
            return Response(
                {"parent_id": "A case cannot be its own parent."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if parent.status == "Duplicate" or case.status == "Duplicate":
            return Response(
                {"parent_id": "Cannot link to or from a merged case."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cycle check: walk the parent chain upward; reject if we encounter
        # `case`. Also enforce max depth (parent-depth + child-tree-depth).
        cursor = parent
        ancestors = []
        while cursor is not None:
            if cursor.id == case.id:
                return Response(
                    {"parent_id": "Linking would create a cycle."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ancestors.append(cursor)
            cursor = cursor.parent

        parent_depth = len(ancestors)  # depth of parent (1 == parent has no parent)
        child_subtree_depth = _max_subtree_depth(case)
        # Resulting tree depth = parent_depth + 1 (case itself) + descendants below it.
        resulting_depth = parent_depth + 1 + child_subtree_depth
        if resulting_depth > TREE_MAX_DEPTH:
            return Response(
                {
                    "parent_id": (
                        f"Case tree is limited to {TREE_MAX_DEPTH} levels."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        case.parent = parent
        case._parent_audit_skip = True
        case.save(update_fields=["parent"])

        _record(
            case,
            "LINKED_PARENT",
            {
                "parent_id": str(parent.id),
                "former_parent_id": (
                    str(former_parent_id) if former_parent_id else None
                ),
            },
            actor=request.profile,
        )
        return Response(
            {
                "id": str(case.id),
                "parent": {
                    "id": str(parent.id),
                    "name": parent.name,
                    "status": parent.status,
                },
            },
            status=status.HTTP_200_OK,
        )


def _max_subtree_depth(case, depth=0, seen=None):
    """Depth of the deepest descendant under ``case``. ``case`` itself = 0."""
    if seen is None:
        seen = set()
    if case.id in seen:
        return depth
    seen.add(case.id)
    children = list(case.children.all())
    if not children:
        return depth
    return max(_max_subtree_depth(c, depth + 1, seen) for c in children)


def _open_descendants(case, out=None):
    """Collect all open (status != Closed) descendants, breadth-first."""
    if out is None:
        out = []
    for child in case.children.all():
        if child.status != "Closed" and child.is_active:
            out.append(child)
        _open_descendants(child, out)
    return out


class CaseCloseWithChildrenView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    @transaction.atomic
    def post(self, request, pk):
        org = request.profile.org
        case = (
            Case.objects.select_for_update()
            .filter(id=pk, org=org)
            .first()
        )
        if case is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        if case.status == "Duplicate":
            return Response(
                {"detail": "Cannot close a merged case."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        resolution_comment = (request.data.get("resolution_comment") or "").strip()
        cascade_override = request.data.get("cascade")
        if cascade_override is None:
            cascade = bool(getattr(org, "auto_close_children_on_parent_close", False))
        else:
            cascade = bool(cascade_override)

        today = date.today()
        # Close the parent first.
        if case.status != "Closed":
            case.status = "Closed"
            case.closed_on = today
            if not case.resolved_at:
                from django.utils import timezone as _tz

                case.resolved_at = _tz.now()
            case.save(
                update_fields=[
                    "status",
                    "closed_on",
                    "resolved_at",
                    "updated_at",
                ]
            )

        cascaded = []
        if cascade:
            descendants = _open_descendants(case)
            for child in descendants:
                child.status = "Closed"
                child.closed_on = today
                if not child.resolved_at:
                    from django.utils import timezone as _tz

                    child.resolved_at = _tz.now()
                child.save(
                    update_fields=[
                        "status",
                        "closed_on",
                        "resolved_at",
                        "updated_at",
                    ]
                )
                _record(
                    child,
                    "PARENT_CLOSED_CASCADE",
                    {
                        "parent_id": str(case.id),
                        "acted_via_cascade": True,
                        "resolution_comment": resolution_comment[:1000],
                    },
                    actor=request.profile,
                )
                cascaded.append(str(child.id))

        return Response(
            {
                "id": str(case.id),
                "status": case.status,
                "cascaded_case_ids": cascaded,
                "resolution_comment": resolution_comment,
            },
            status=status.HTTP_200_OK,
        )
