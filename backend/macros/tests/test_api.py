"""End-to-end API tests for /api/macros/."""

import pytest

from macros.models import Macro

LIST_URL = "/api/macros/"


def _detail_url(pk):
    return f"/api/macros/{pk}/"


def _render_url(pk):
    return f"/api/macros/{pk}/render/"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class TestAuth:
    def test_unauthenticated_list(self, unauthenticated_client):
        resp = unauthenticated_client.get(LIST_URL)
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# List visibility
# ---------------------------------------------------------------------------


class TestList:
    def test_user_sees_org_and_own_personal(
        self, user_client, org_macro, personal_macro
    ):
        resp = user_client.get(LIST_URL)
        assert resp.status_code == 200
        ids = {row["id"] for row in resp.json()["results"]}
        assert str(org_macro.id) in ids
        assert str(personal_macro.id) in ids

    def test_user_does_not_see_others_personal(
        self, user_client, org_a, admin_profile, org_macro
    ):
        # A personal macro owned by the admin must not surface to user_client.
        Macro.objects.create(
            org=org_a,
            title="Admin private",
            body="x",
            scope=Macro.SCOPE_PERSONAL,
            owner=admin_profile,
        )
        resp = user_client.get(LIST_URL)
        titles = {row["title"] for row in resp.json()["results"]}
        assert "Admin private" not in titles
        assert org_macro.title in titles

    def test_search_filter(self, user_client, org_a):
        Macro.objects.create(org=org_a, title="Greeting", body="hello")
        Macro.objects.create(org=org_a, title="Closer", body="bye")
        resp = user_client.get(LIST_URL + "?search=greet")
        titles = {row["title"] for row in resp.json()["results"]}
        assert titles == {"Greeting"}

    def test_active_filter(self, user_client, org_a):
        Macro.objects.create(
            org=org_a, title="alive", body="x", is_active=True
        )
        Macro.objects.create(
            org=org_a, title="dead", body="x", is_active=False
        )
        resp = user_client.get(LIST_URL + "?active=true")
        titles = {row["title"] for row in resp.json()["results"]}
        assert titles == {"alive"}

    def test_cross_org_isolation(
        self, org_b_client, org_macro, personal_macro
    ):
        resp = org_b_client.get(LIST_URL)
        assert resp.status_code == 200
        # Org A macros must not leak into org B's list.
        ids = {row["id"] for row in resp.json()["results"]}
        assert str(org_macro.id) not in ids
        assert str(personal_macro.id) not in ids


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreate:
    def test_admin_can_create_org_macro(self, admin_client):
        resp = admin_client.post(
            LIST_URL,
            {"title": "Hello", "body": "Hi %customer_name%", "scope": "org"},
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["scope"] == "org"
        assert body["owner"] is None

    def test_user_cannot_create_org_macro(self, user_client):
        resp = user_client.post(
            LIST_URL,
            {"title": "Hello", "body": "x", "scope": "org"},
            format="json",
        )
        assert resp.status_code == 403

    def test_user_can_create_personal_macro_owned_by_self(
        self, user_client, user_profile
    ):
        resp = user_client.post(
            LIST_URL,
            {"title": "Mine", "body": "x", "scope": "personal"},
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["scope"] == "personal"
        assert body["owner"] == str(user_profile.id)

    def test_admin_personal_macro_owned_by_admin(self, admin_client, admin_profile):
        resp = admin_client.post(
            LIST_URL,
            {"title": "Mine", "body": "x", "scope": "personal"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["owner"] == str(admin_profile.id)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_admin_can_edit_org_macro(self, admin_client, org_macro):
        resp = admin_client.patch(
            _detail_url(org_macro.id), {"title": "Renamed"}, format="json"
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed"

    def test_user_cannot_edit_org_macro(self, user_client, org_macro):
        resp = user_client.patch(
            _detail_url(org_macro.id), {"title": "Renamed"}, format="json"
        )
        assert resp.status_code == 403

    def test_user_can_edit_own_personal(self, user_client, personal_macro):
        resp = user_client.patch(
            _detail_url(personal_macro.id),
            {"title": "Renamed personal"},
            format="json",
        )
        assert resp.status_code == 200

    def test_user_cannot_edit_others_personal(
        self, user_client, org_a, admin_profile
    ):
        other = Macro.objects.create(
            org=org_a,
            title="theirs",
            body="x",
            scope=Macro.SCOPE_PERSONAL,
            owner=admin_profile,
        )
        resp = user_client.patch(
            _detail_url(other.id), {"title": "stealing"}, format="json"
        )
        # Personal macros owned by others are 403 (visible-to-admin only),
        # never 200.
        assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDelete:
    def test_org_macro_soft_delete(self, admin_client, org_macro):
        resp = admin_client.delete(_detail_url(org_macro.id))
        assert resp.status_code == 204
        org_macro.refresh_from_db()
        assert org_macro.is_active is False
        # Row still exists.
        assert Macro.objects.filter(pk=org_macro.id).exists()

    def test_personal_macro_hard_delete(self, user_client, personal_macro):
        resp = user_client.delete(_detail_url(personal_macro.id))
        assert resp.status_code == 204
        assert not Macro.objects.filter(pk=personal_macro.id).exists()


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


class TestRender:
    def test_render_substitutes_placeholders(
        self, user_client, org_macro, case_factory, contact_factory
    ):
        contact = contact_factory(first_name="Liz", last_name="Lopez")
        case = case_factory(contact=contact)
        resp = user_client.post(
            _render_url(org_macro.id),
            {"case_id": str(case.id)},
            format="json",
        )
        assert resp.status_code == 200
        rendered = resp.json()["rendered_body"]
        assert "Liz Lopez" in rendered
        assert "Test Organization A" in rendered

    def test_render_increments_usage_count(
        self, user_client, org_macro, case_factory
    ):
        before = org_macro.usage_count
        case = case_factory()
        resp = user_client.post(
            _render_url(org_macro.id),
            {"case_id": str(case.id)},
            format="json",
        )
        assert resp.status_code == 200
        org_macro.refresh_from_db()
        assert org_macro.usage_count == before + 1

    def test_render_inactive_macro_rejected(
        self, admin_client, org_macro, case_factory
    ):
        org_macro.is_active = False
        org_macro.save(update_fields=["is_active"])
        case = case_factory()
        resp = admin_client.post(
            _render_url(org_macro.id),
            {"case_id": str(case.id)},
            format="json",
        )
        assert resp.status_code == 400

    def test_render_missing_case_id_rejected(self, user_client, org_macro):
        resp = user_client.post(
            _render_url(org_macro.id), {}, format="json"
        )
        assert resp.status_code == 400

    def test_render_cross_org_case_404(
        self, user_client, org_b, org_macro
    ):
        from cases.models import Case

        # Build a case in org_b directly. RLS is the safety net but the view
        # also explicitly filters by `org=request.profile.org`, which is what
        # this test exercises.
        case = Case.objects.create(
            org=org_b, name="other", status="New", priority="Normal"
        )
        resp = user_client.post(
            _render_url(org_macro.id),
            {"case_id": str(case.id)},
            format="json",
        )
        assert resp.status_code == 404

    def test_render_other_users_personal_macro_404(
        self, user_client, org_a, admin_profile, case_factory
    ):
        other = Macro.objects.create(
            org=org_a,
            title="theirs",
            body="x",
            scope=Macro.SCOPE_PERSONAL,
            owner=admin_profile,
        )
        case = case_factory()
        resp = user_client.post(
            _render_url(other.id),
            {"case_id": str(case.id)},
            format="json",
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# unknown_placeholders serializer field
# ---------------------------------------------------------------------------


class TestUnknownPlaceholders:
    """Backend-authoritative warning surface for typoed/unsupported tokens.

    The web UI does its own client-side check for live feedback, but mobile
    and API consumers rely on this field — and the workspace rule says
    every UX constraint must also exist server-side.
    """

    def test_clean_body_returns_empty_list(self, user_client, org_macro):
        resp = user_client.get(LIST_URL)
        rows = {row["id"]: row for row in resp.json()["results"]}
        assert rows[str(org_macro.id)]["unknown_placeholders"] == []

    def test_typo_surfaced_on_create(self, admin_client):
        resp = admin_client.post(
            LIST_URL,
            {
                "title": "Greeting",
                "body": "Hi %custmer_name%, this is %agent_name%.",
                "scope": "org",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["unknown_placeholders"] == ["%custmer_name%"]

    def test_typo_surfaced_on_list_and_detail(self, user_client, org_a):
        macro = Macro.objects.create(
            org=org_a,
            title="Bad",
            body="Hi %custmer_name%, priority %priority%.",
            scope=Macro.SCOPE_ORG,
        )
        list_resp = user_client.get(LIST_URL)
        row = next(r for r in list_resp.json()["results"] if r["id"] == str(macro.id))
        assert row["unknown_placeholders"] == ["%custmer_name%", "%priority%"]

        detail_resp = user_client.get(_detail_url(macro.id))
        assert detail_resp.json()["unknown_placeholders"] == [
            "%custmer_name%",
            "%priority%",
        ]

    def test_field_updates_after_patch(self, admin_client, org_macro):
        # Sanity: editing the body re-derives the field from the new text.
        resp = admin_client.patch(
            _detail_url(org_macro.id),
            {"body": "Now with %typo%"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["unknown_placeholders"] == ["%typo%"]

    def test_creation_is_not_blocked_by_unknown_placeholder(self, admin_client):
        # Soft warning, not a save-blocker — matches `render_macro`'s
        # leave-literal stance for unknown tokens.
        resp = admin_client.post(
            LIST_URL,
            {
                "title": "Future",
                "body": "Priority is %priority%",
                "scope": "org",
            },
            format="json",
        )
        assert resp.status_code == 201
