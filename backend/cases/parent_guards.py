"""The parent/child linking rules, in one place both write paths can call.

``Case.clean()`` declares four rules about linking a case under a parent: no
self-parent, no cycle, no more than ``Case.PARENT_MAX_DEPTH`` levels, and
nothing linked to or from a merged (``Duplicate``) case. Nothing on the save
path calls ``full_clean()`` and DRF never calls ``Model.clean()``, so those
rules only ever ran where a view or serializer reimplemented them.

``CaseLinkParentView`` did reimplement all four. ``CaseSerializer`` reimplemented
one and a half, and ``parent`` is writable there, so
``PATCH /api/cases/<id>/ {"parent": ...}`` could store a cycle that the link
endpoint's ancestor walk then followed forever. Writing the rules a third time
in the serializer would have set up the same drift again, which is why they
live here instead.
"""

from cases.models import Case

MAX_DEPTH = Case.PARENT_MAX_DEPTH


def max_subtree_depth(case, depth=0, seen=None):
    """Depth of the deepest descendant under ``case``. ``case`` itself = 0."""
    if seen is None:
        seen = set()
    if case.id in seen:
        return depth
    seen.add(case.id)
    children = list(case.children.all())
    if not children:
        return depth
    return max(max_subtree_depth(c, depth + 1, seen) for c in children)


def check_parent_link(parent, *, case=None, case_status=None):
    """Return a message explaining why this link is refused, or ``None``.

    ``parent`` is the case being linked to, already resolved and confirmed to
    be in the caller's org. ``case`` is the record being moved, or ``None`` on
    create, where there is no row yet to close a cycle with and no subtree to
    carry along. ``case_status`` overrides the stored status, for a request
    that changes status and parent together.

    A message rather than a raised exception: the two callers report errors
    differently (a DRF ``ValidationError`` against the ``parent`` field, and a
    hand-built 400 body keyed ``parent_id``), and neither shape belongs here.
    """
    if parent is None:
        return None

    if case is not None and parent.id == case.id:
        return "A case cannot be its own parent."

    status = case_status if case_status is not None else getattr(case, "status", None)
    if parent.status == "Duplicate" or status == "Duplicate":
        return "Cannot link to or from a merged case."

    # Walk up from the proposed parent. `seen` is not redundant with the
    # `case.id` test: a cycle that does not pass through `case` still makes
    # this loop run forever, and one such cycle is reachable in any database
    # written before this guard existed.
    seen = set()
    cursor = parent
    depth_above = 0
    while cursor is not None:
        if case is not None and cursor.id == case.id:
            return "Linking would create a cycle."
        if cursor.id in seen:
            return (
                "This case's parent chain already contains a cycle, so nothing "
                "can be linked under it."
            )
        seen.add(cursor.id)
        depth_above += 1
        cursor = cursor.parent

    # Levels above the parent, plus the parent, plus whatever `case` brings
    # with it. Re-parenting moves a whole subtree, so a case with children of
    # its own does not fit everywhere a leaf would.
    subtree_below = max_subtree_depth(case) if case is not None else 0
    if depth_above + 1 + subtree_below > MAX_DEPTH:
        return f"Case tree is limited to {MAX_DEPTH} levels."

    return None
