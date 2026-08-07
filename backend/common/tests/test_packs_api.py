import pytest

from common.middleware.rls_context import RequireOrgContext
from common.models import User


@pytest.fixture
def orgless_user():
    return User.objects.create_user(email="noorg@test.com", password="testpass123")


@pytest.fixture
def orgless_client(orgless_user):
    """
    An authenticated JWT client whose token carries NO org_id claim. The
    shape of a user who has signed up but not yet created or joined an org.
    This is the exact audience GET /api/packs/ must serve (the pack chooser
    lives on the org-creation page); it's also the audience the write and
    destroy pack endpoints must keep rejecting.
    """
    from conftest import _make_authenticated_client

    return _make_authenticated_client(orgless_user, None, None)


@pytest.mark.django_db
class TestPackAPI:
    def test_list_is_available_to_any_member(self, user_client):
        res = user_client.get("/api/packs/")
        assert res.status_code == 200
        assert {p["id"] for p in res.json()["packs"]} >= {"real-estate"}

    def test_admin_can_apply(self, admin_client, org_a):
        res = admin_client.post("/api/packs/real-estate/apply/")
        assert res.status_code == 200
        assert res.json()["report"]["created"]

    def test_non_admin_cannot_apply(self, user_client):
        res = user_client.post("/api/packs/real-estate/apply/")
        assert res.status_code == 403

    def test_non_admin_cannot_clear_sample_data(self, user_client):
        res = user_client.delete("/api/packs/sample-data/")
        assert res.status_code == 403

    def test_unknown_pack_is_404(self, admin_client):
        assert admin_client.post("/api/packs/nope/apply/").status_code == 404

    def test_traversal_pack_id_is_404_not_a_file_read(self, admin_client):
        # %2F decodes to "/" before URL resolution, so this never reaches
        # PackApplyView at all: it 404s at the Django router, as a plain
        # HTML page, not the view's {"error": ..., "errors": "Unknown pack."}
        # JSON shape. That still proves no file read happened, but it does
        # NOT exercise get_pack()/the registry lookup this test is named for.
        res = admin_client.post("/api/packs/..%2F..%2Fetc%2Fpasswd/apply/")
        assert res.status_code == 404

        # A slash-free traversal-shaped id (backslash-encoded, so the router
        # treats it as one path segment) DOES reach the view and get_pack().
        # This is what actually proves the registry lookup, a dict get(),
        # is what turns a path-shaped id into a 404, not a filesystem call.
        res = admin_client.post("/api/packs/..%5C..%5Cwindows%5Cwin.ini/apply/")
        assert res.status_code == 404
        assert res.json() == {"error": True, "errors": "Unknown pack."}

    def test_org_in_body_is_ignored(self, admin_client, org_a, org_b):
        res = admin_client.post("/api/packs/real-estate/apply/", {"org": str(org_b.id)})
        assert res.status_code == 200
        from leads.models import LeadPipeline

        assert LeadPipeline.objects.filter(org=org_b).count() == 0
        assert LeadPipeline.objects.filter(org=org_a).count() == 1

    def test_unauthenticated_is_rejected(self, unauthenticated_client):
        assert unauthenticated_client.get("/api/packs/").status_code in (401, 403)

    def test_admin_can_clear_sample_data(self, admin_client, org_a):
        admin_client.post("/api/packs/real-estate/apply/")
        res = admin_client.delete("/api/packs/sample-data/")
        assert res.status_code == 200
        assert res.json()["deleted"] >= 8

    def test_clear_sample_data_does_not_touch_another_org(
        self, admin_client, org_b_client, org_a, org_b
    ):
        # org_b_client is org_b's own ADMIN (profile_b, role=ADMIN. See
        # conftest.py), not admin_client's org_a profile: applying to org_b
        # must use an org_b actor now that apply_pack rejects a mismatched
        # (org, actor) pair.
        admin_client.post("/api/packs/real-estate/apply/")
        org_b_client.post("/api/packs/real-estate/apply/")

        res = org_b_client.delete("/api/packs/sample-data/")
        assert res.status_code == 200

        from leads.models import Lead

        assert Lead.objects.filter(org=org_b, is_sample=True).count() == 0
        assert Lead.objects.filter(org=org_a, is_sample=True).count() >= 8

    def test_org_in_delete_body_is_ignored(self, admin_client, org_a, org_b):
        admin_client.post("/api/packs/real-estate/apply/")

        res = admin_client.delete(
            "/api/packs/sample-data/", {"org": str(org_b.id)}, format="json"
        )
        assert res.status_code == 200

        from leads.models import Lead

        # The delete acted on request.profile.org (org_a) regardless of the
        # org id smuggled into the body.
        assert Lead.objects.filter(org=org_a, is_sample=True).count() == 0


@pytest.mark.django_db
class TestPackListNoOrgContext:
    """
    GET /api/packs/ must render for a user who has no org yet (the pack
    chooser lives on the org-creation page, before any org_id claim exists),
    while POST .../apply/ and DELETE .../sample-data/ must keep requiring
    org context for that same user. This is the RequireOrgContext exact-match
    exemption (EXEMPT_EXACT_PATHS) plus PackListView dropping HasOrgContext.
    """

    def test_list_available_with_no_org_context(self, orgless_client):
        res = orgless_client.get("/api/packs/")
        assert res.status_code == 200
        assert {p["id"] for p in res.json()["packs"]} >= {"real-estate"}

    def test_apply_still_requires_org_context(self, orgless_client):
        # Must NOT have become reachable just because list did.
        res = orgless_client.post("/api/packs/real-estate/apply/")
        assert res.status_code == 403

    def test_sample_data_delete_still_requires_org_context(self, orgless_client):
        res = orgless_client.delete("/api/packs/sample-data/")
        assert res.status_code == 403

    def test_packs_is_exempt_by_exact_match_only(self):
        # Pins the exemption to the exact-match list. If a later refactor
        # moves "/api/packs/" into the prefix-matched EXEMPT_PATHS, this
        # fails, and so would the two tests above, since a prefix match
        # would also exempt /api/packs/<id>/apply/ and
        # /api/packs/sample-data/ from tenant-context enforcement.
        assert "/api/packs/" in RequireOrgContext.EXEMPT_EXACT_PATHS
        assert "/api/packs/" not in RequireOrgContext.EXEMPT_PATHS
