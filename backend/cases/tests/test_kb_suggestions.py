"""Tests for the agent-side KB suggester endpoint.

The customer-facing public KB site is deliberately out of scope (see
docs/cases/tier2/IMPLEMENTATION_STATUS.md kb-frontend section). What we
verify here is just the typeahead feeding the comment composer:
published-only filter, q-search vs case-seed fallback, snippet, RLS.
"""

import pytest

from cases.models import Solution


@pytest.fixture
def published_solutions(org_a):
    """Mix of published + draft so we can confirm drafts never leak."""
    s1 = Solution.objects.create(
        org=org_a,
        title="Reset your password",
        description="Click forgot password on the sign-in page.",
        status="approved",
        is_published=True,
    )
    s2 = Solution.objects.create(
        org=org_a,
        title="Two-factor authentication",
        description="Enable 2FA in account settings.",
        status="approved",
        is_published=True,
    )
    s3 = Solution.objects.create(
        org=org_a,
        title="Internal draft about passwords",
        description="Don't show me — I'm a draft.",
        status="draft",
        is_published=False,
    )
    return s1, s2, s3


class TestSolutionSuggestionsAuth:
    def test_unauthenticated(self, unauthenticated_client, case_a):
        resp = unauthenticated_client.get(
            f"/api/cases/{case_a.id}/solution-suggestions/?q=password"
        )
        assert resp.status_code in (401, 403)

    def test_unknown_case_returns_404(self, admin_client):
        resp = admin_client.get(
            "/api/cases/00000000-0000-0000-0000-000000000000/solution-suggestions/?q=x"
        )
        assert resp.status_code == 404


class TestSolutionSuggestionsSearch:
    def test_q_filters_to_matches(self, admin_client, case_a, published_solutions):
        resp = admin_client.get(
            f"/api/cases/{case_a.id}/solution-suggestions/?q=password"
        )
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.data["results"]]
        assert "Reset your password" in titles
        assert "Two-factor authentication" not in titles

    def test_drafts_never_leak(self, admin_client, case_a, published_solutions):
        # The draft in the fixture also has "passwords" in its description.
        resp = admin_client.get(
            f"/api/cases/{case_a.id}/solution-suggestions/?q=password"
        )
        titles = [r["title"] for r in resp.data["results"]]
        assert "Internal draft about passwords" not in titles

    def test_limit_capped(self, admin_client, case_a, org_a):
        # Many published solutions, default limit=5.
        for i in range(10):
            Solution.objects.create(
                org=org_a,
                title=f"Article {i}",
                description="Common phrase that matches. " * 3,
                status="approved",
                is_published=True,
            )
        resp = admin_client.get(
            f"/api/cases/{case_a.id}/solution-suggestions/?q=common"
        )
        assert resp.status_code == 200
        assert len(resp.data["results"]) == 5

    def test_explicit_limit_respected(self, admin_client, case_a, org_a):
        for i in range(10):
            Solution.objects.create(
                org=org_a,
                title=f"Article {i}",
                description="X marks the spot.",
                status="approved",
                is_published=True,
            )
        resp = admin_client.get(
            f"/api/cases/{case_a.id}/solution-suggestions/?q=marks&limit=3"
        )
        assert len(resp.data["results"]) == 3


class TestSolutionSuggestionsSeed:
    def test_empty_q_seeds_from_case_name(
        self, admin_client, case_a, published_solutions
    ):
        # case_a.name = "Bug in login page" → seed picks up "login" & "page".
        # Add a published solution mentioning "login".
        Solution.objects.create(
            org=case_a.org,
            title="Login troubleshooting",
            description="Steps for the login flow.",
            status="approved",
            is_published=True,
        )
        resp = admin_client.get(f"/api/cases/{case_a.id}/solution-suggestions/")
        assert resp.status_code == 200
        titles = [r["title"] for r in resp.data["results"]]
        assert "Login troubleshooting" in titles

    def test_empty_q_falls_back_to_recent_when_no_seed_match(
        self, admin_client, case_a, org_a
    ):
        # No matches against "Bug in login page" terms — endpoint falls back
        # to the most-recent published solutions.
        Solution.objects.create(
            org=org_a,
            title="Unrelated topic",
            description="Has nothing to do with the case.",
            status="approved",
            is_published=True,
        )
        resp = admin_client.get(f"/api/cases/{case_a.id}/solution-suggestions/")
        assert resp.status_code == 200
        # Should not 500; should return the unrelated row as a recent fallback.
        assert resp.data["count"] >= 1


class TestSolutionSuggestionsSnippet:
    def test_snippet_truncated(self, admin_client, case_a, org_a):
        long_text = "abc " * 200  # 800 chars.
        Solution.objects.create(
            org=org_a,
            title="Big article",
            description=long_text,
            status="approved",
            is_published=True,
        )
        resp = admin_client.get(
            f"/api/cases/{case_a.id}/solution-suggestions/?q=abc"
        )
        for row in resp.data["results"]:
            if row["title"] == "Big article":
                assert len(row["snippet"]) <= 200
                assert row["snippet"].endswith("…")


class TestSolutionSuggestionsRls:
    def test_cross_org_solutions_invisible(
        self, admin_client, case_a, org_b
    ):
        Solution.objects.create(
            org=org_b,
            title="Other org password reset",
            description="This belongs to a different tenant.",
            status="approved",
            is_published=True,
        )
        resp = admin_client.get(
            f"/api/cases/{case_a.id}/solution-suggestions/?q=password"
        )
        titles = [r["title"] for r in resp.data["results"]]
        assert "Other org password reset" not in titles

    def test_cross_org_case_returns_404(
        self, admin_client, case_b
    ):
        # admin_client is in org_a; case_b lives in org_b.
        resp = admin_client.get(
            f"/api/cases/{case_b.id}/solution-suggestions/?q=password"
        )
        assert resp.status_code == 404
