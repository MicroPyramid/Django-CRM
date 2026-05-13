"""Agent-facing knowledge-base helpers.

The full kb-frontend spec calls for a customer-facing KB site too. We
ship only the agent-side suggester here — see
docs/cases/tier2/IMPLEMENTATION_STATUS.md "kb-frontend" section for the
deliberate cut. The endpoint feeds the comment composer's typeahead.
"""

from __future__ import annotations

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Case, Solution
from common.permissions import HasOrgContext


_SNIPPET_MAX = 200
_DEFAULT_LIMIT = 5
_MAX_LIMIT = 20


def _snippet(text: str | None) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= _SNIPPET_MAX:
        return text
    return text[: _SNIPPET_MAX - 1].rstrip() + "…"


def _seed_terms(case: Case) -> list[str]:
    """Seed terms when q is empty: pull a handful of meaningful words from
    the case name + description so the agent gets useful suggestions on
    first focus instead of an empty list.
    """
    pieces: list[str] = []
    for raw in (case.name or "", case.description or ""):
        for word in raw.split():
            cleaned = "".join(ch for ch in word if ch.isalnum() or ch in "-_").lower()
            if len(cleaned) >= 4:
                pieces.append(cleaned)
            if len(pieces) >= 6:
                break
        if len(pieces) >= 6:
            break
    return pieces


class SolutionSuggestionsView(APIView):
    """`GET /api/cases/<pk>/solution-suggestions/?q=&limit=`.

    Returns the top N published solutions in the same org whose title or
    description matches the search term. `?q=` is optional — when blank,
    the case's own name + description seed the search so the panel is
    useful on first focus.
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["Cases"],
        parameters=[
            OpenApiParameter("q", str, description="Search query"),
            OpenApiParameter(
                "limit", int, description="Max results, default 5, capped at 20"
            ),
        ],
    )
    def get(self, request, pk):
        org = request.profile.org
        case = Case.objects.filter(pk=pk, org=org).first()
        if case is None:
            return Response({"error": "Case not found"}, status=404)

        try:
            limit = int(request.query_params.get("limit", _DEFAULT_LIMIT))
        except ValueError:
            limit = _DEFAULT_LIMIT
        limit = max(1, min(_MAX_LIMIT, limit))

        q = (request.query_params.get("q") or "").strip()
        published = Solution.objects.filter(org=org, is_published=True)

        if q:
            results = (
                published.filter(Q(title__icontains=q) | Q(description__icontains=q))
                .order_by("-updated_at")[:limit]
            )
        else:
            # Seed from the case so the panel is useful on first focus. If
            # there are no seed terms, or the seed-term filter produces zero
            # matches, fall back to the most-recent published solutions —
            # the agent should always see *something* on first focus.
            terms = _seed_terms(case)
            results = []
            if terms:
                seed_filter = Q()
                for term in terms:
                    seed_filter |= Q(title__icontains=term) | Q(
                        description__icontains=term
                    )
                results = list(
                    published.filter(seed_filter).order_by("-updated_at")[:limit]
                )
            if not results:
                results = list(published.order_by("-updated_at")[:limit])

        data = [
            {
                "id": str(s.id),
                "title": s.title,
                "snippet": _snippet(s.description),
                # Full body included so the picker can paste without a
                # second roundtrip. Keeps the widget snappy on a slow link.
                "body": s.description or "",
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in results
        ]
        return Response({"results": data, "count": len(data), "q": q})
