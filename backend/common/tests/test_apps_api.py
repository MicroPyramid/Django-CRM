"""The industry apps API: ``/api/apps/`` and the ``/api/packs/<id>/apply/`` alias.

Every write is admin-only and every refusal is tested beside its allowed path.
"""

from unittest import mock

import pytest
from django.db import connection

from common.apps_catalogue import install_app
from common.models import InstalledApp, PackApplication
from common.packs.loader import get_registry
from common.testing import rls_org, rls_policy_gaps, set_modules_off
from leads.models import Lead, LeadPipeline

APP = "real-estate"
APP_KEYS = {
    "id",
    "name",
    "description",
    "version",
    "status",
    "installed_version",
    "update_available",
    "skipped_modules",
    "installed_at",
    "installed_by_details",
}


def _app(response, app_id=APP):
    return next(a for a in response.json()["apps"] if a["id"] == app_id)


class TestList:
    def test_any_member_reads_the_catalogue_in_order(self, user_client):
        res = user_client.get("/api/apps/")

        assert res.status_code == 200
        apps = res.json()["apps"]
        assert [a["id"] for a in apps] == list(get_registry())
        for app in apps:
            assert set(app) == APP_KEYS
            assert app["status"] == "not_installed"
            assert app["installed_version"] is None
            assert app["update_available"] is False
            assert app["skipped_modules"] == []
            assert app["installed_at"] is None
            assert app["installed_by_details"] is None

    def test_an_installed_app_shows_who_and_when(
        self, user_client, admin_profile, org_a
    ):
        admin_profile.user.name = "Admin Person"
        admin_profile.user.save(update_fields=["name"])
        install_app(org_a, APP, admin_profile, sample_data=False)

        app = _app(user_client.get("/api/apps/"))

        assert app["status"] == "installed"
        assert app["installed_version"] == app["version"]
        assert app["installed_at"]
        assert app["installed_by_details"] == {
            "id": str(admin_profile.id),
            "name": "Admin Person",
        }

    def test_skipped_modules_and_update_available(
        self, user_client, admin_profile, org_a
    ):
        set_modules_off(org_a, "tickets")
        install_app(org_a, APP, admin_profile, sample_data=False)

        app = _app(user_client.get("/api/apps/"))
        assert (app["skipped_modules"], app["update_available"]) == (["tickets"], False)

        set_modules_off(org_a)
        app = _app(user_client.get("/api/apps/"))
        assert (app["skipped_modules"], app["update_available"]) == (["tickets"], True)

    def test_update_available_says_whether_upgrade_has_work(
        self, admin_client, admin_profile, org_a
    ):
        """Same version: parts skipped for an off module are the update, and
        the version stays. A newer version is an update when it adds something.
        Nothing to add is no update and a 409."""
        set_modules_off(org_a, "tickets")
        install_app(org_a, APP, admin_profile, sample_data=False)
        version = get_registry()[APP]["version"]
        set_modules_off(org_a)
        assert _app(admin_client.get("/api/apps/"))["update_available"] is True

        res = admin_client.post(f"/api/apps/{APP}/upgrade/")

        assert res.status_code == 200
        app = res.json()["app"]
        assert (app["installed_version"], app["update_available"]) == (version, False)
        assert app["skipped_modules"] == []
        assert admin_client.post(f"/api/apps/{APP}/upgrade/").status_code == 409

        with mock.patch.dict(get_registry()):
            pack = get_registry()[APP]
            get_registry()[APP] = {**pack, "version": version + 1}
            app = _app(admin_client.get("/api/apps/"))
            assert (app["version"], app["update_available"]) == (version + 1, False)
            assert admin_client.post(f"/api/apps/{APP}/upgrade/").status_code == 409

            tags = [*pack["tags"], {"name": "Waterfront"}]
            get_registry()[APP] = {**pack, "version": version + 1, "tags": tags}
            assert _app(admin_client.get("/api/apps/"))["update_available"] is True
            res = admin_client.post(f"/api/apps/{APP}/upgrade/")
            assert res.status_code == 200
            assert res.json()["app"]["installed_version"] == version + 1
            assert admin_client.post(f"/api/apps/{APP}/upgrade/").status_code == 409

    def test_another_orgs_install_is_not_shown(
        self, org_b_client, admin_profile, org_a
    ):
        install_app(org_a, APP, admin_profile, sample_data=False)

        app = _app(org_b_client.get("/api/apps/"))

        assert app["status"] == "not_installed"
        assert app["installed_by_details"] is None

    def test_a_removed_app(self, admin_client, admin_profile, org_a):
        install_app(org_a, APP, admin_profile, sample_data=False)
        admin_client.post(f"/api/apps/{APP}/remove/")

        app = _app(admin_client.get("/api/apps/"))

        assert app["status"] == "removed"
        assert app["update_available"] is False

    def test_unauthenticated_is_refused(self, unauthenticated_client):
        assert unauthenticated_client.get("/api/apps/").status_code in (401, 403)


class TestPreview:
    def test_admin_previews_an_install(self, admin_client):
        res = admin_client.get(f"/api/apps/{APP}/preview/", {"action": "install"})

        assert res.status_code == 200
        body = res.json()
        assert set(body) == {"action", "items", "sample_data"}
        assert body["action"] == "install"
        assert body["items"]
        for item in body["items"]:
            assert set(item) == {"type", "target", "label", "effect"}
        assert set(body["sample_data"]) == {"offered", "default_on", "records"}

    @pytest.mark.parametrize("action", ["install", "upgrade", "remove"])
    def test_a_member_is_refused(self, user_client, action):
        res = user_client.get(f"/api/apps/{APP}/preview/", {"action": action})
        assert res.status_code == 403

    def test_an_unknown_app_is_404(self, admin_client):
        res = admin_client.get("/api/apps/nope/preview/", {"action": "install"})
        assert res.status_code == 404

    @pytest.mark.parametrize("action", [None, "", "delete", "INSTALL"])
    def test_an_unknown_action_is_400(self, admin_client, action):
        params = {} if action is None else {"action": action}
        res = admin_client.get(f"/api/apps/{APP}/preview/", params)
        assert res.status_code == 400

    def test_an_impossible_action_is_409(self, admin_client):
        res = admin_client.get(f"/api/apps/{APP}/preview/", {"action": "remove"})
        assert res.status_code == 409

    def test_it_writes_nothing(self, admin_client, org_a):
        admin_client.get(f"/api/apps/{APP}/preview/", {"action": "install"})

        assert not InstalledApp.objects.exists()
        assert not LeadPipeline.objects.filter(org=org_a).exists()
        assert not PackApplication.objects.exists()


class TestActions:
    def test_install_upgrade_and_remove_answer_the_app(self, admin_client, org_a):
        res = admin_client.post(
            f"/api/apps/{APP}/install/", {"sample_data": False}, format="json"
        )
        assert res.status_code == 200
        assert set(res.json()) == {"app"}
        assert res.json()["app"]["status"] == "installed"
        assert set(res.json()["app"]) == APP_KEYS
        assert not Lead.objects.filter(org=org_a).exists()

        assert admin_client.post(f"/api/apps/{APP}/upgrade/").status_code == 409

        res = admin_client.post(f"/api/apps/{APP}/remove/")
        assert res.status_code == 200
        assert res.json()["app"]["status"] == "removed"
        assert admin_client.post(f"/api/apps/{APP}/remove/").status_code == 409

    def test_install_twice_is_409(self, admin_client):
        admin_client.post(f"/api/apps/{APP}/install/", {"sample_data": False})
        res = admin_client.post(f"/api/apps/{APP}/install/", {"sample_data": False})
        assert res.status_code == 409

    def test_sample_data_follows_the_request(self, admin_client, org_a):
        res = admin_client.post(
            f"/api/apps/{APP}/install/", {"sample_data": True}, format="json"
        )
        assert res.status_code == 200
        assert Lead.objects.filter(org=org_a, is_sample=True).exists()

    def test_sample_data_defaults_to_the_preview_default(self, admin_client, org_a):
        Lead.objects.create(org=org_a, title="A real one")

        assert admin_client.post(f"/api/apps/{APP}/install/").status_code == 200

        assert not Lead.objects.filter(org=org_a, is_sample=True).exists()

    def test_sample_data_must_be_a_boolean(self, admin_client):
        res = admin_client.post(
            f"/api/apps/{APP}/install/", {"sample_data": "lots"}, format="json"
        )
        assert res.status_code == 400
        assert not InstalledApp.objects.exists()

    @pytest.mark.parametrize("action", ["install", "upgrade", "remove"])
    def test_a_member_is_refused(self, user_client, admin_profile, org_a, action):
        if action != "install":
            install_app(org_a, APP, admin_profile, sample_data=False)
        before = list(InstalledApp.objects.values())

        res = user_client.post(f"/api/apps/{APP}/{action}/", {"sample_data": False})

        assert res.status_code == 403
        assert list(InstalledApp.objects.values()) == before

    @pytest.mark.parametrize("action", ["install", "upgrade", "remove"])
    def test_an_unknown_app_is_404(self, admin_client, action):
        assert admin_client.post(f"/api/apps/nope/{action}/").status_code == 404

    def test_the_org_comes_from_the_profile(self, admin_client, org_a, org_b):
        res = admin_client.post(
            f"/api/apps/{APP}/install/",
            {"sample_data": False, "org": str(org_b.id)},
            format="json",
        )

        assert res.status_code == 200
        assert InstalledApp.objects.filter(org=org_a).count() == 1
        assert not InstalledApp.objects.filter(org=org_b).exists()

    def test_another_org_cannot_remove_this_orgs_app(
        self, org_b_client, admin_profile, org_a
    ):
        install_app(org_a, APP, admin_profile, sample_data=False)

        assert org_b_client.post(f"/api/apps/{APP}/remove/").status_code == 409

        assert InstalledApp.objects.get(org=org_a).status == "installed"

    def test_the_apps_routes_are_core(self, admin_client, org_a):
        set_modules_off(org_a, "leads", "deals", "tickets", "tasks", "invoices")

        assert admin_client.get("/api/apps/").status_code == 200


class TestPacksAlias:
    """Phones already in the stores apply a pack; that now installs the app."""

    def test_apply_installs_with_sample_data_and_keeps_its_shape(
        self, admin_client, org_a
    ):
        res = admin_client.post(f"/api/packs/{APP}/apply/")

        assert res.status_code == 200
        report = res.json()["report"]
        assert set(report) == {"created", "skipped", "failed"}
        assert {"type": "lead_pipeline", "name": "Sales"} in report["created"]
        row = InstalledApp.objects.get(org=org_a, app_id=APP)
        assert row.status == "installed"
        assert Lead.objects.filter(org=org_a, is_sample=True).exists()

    def test_apply_on_an_installed_app_creates_nothing(
        self, admin_client, org_a, admin_profile
    ):
        install_app(org_a, APP, admin_profile, sample_data=False)
        LeadPipeline.objects.filter(org=org_a, name="Sales").delete()

        res = admin_client.post(f"/api/packs/{APP}/apply/")

        assert res.status_code == 200
        assert res.json()["report"]["created"] == []
        assert not LeadPipeline.objects.filter(org=org_a, name="Sales").exists()
        assert PackApplication.objects.filter(org=org_a).count() == 1

    def test_apply_reinstalls_a_removed_app(self, admin_client, org_a, admin_profile):
        install_app(org_a, APP, admin_profile, sample_data=False)
        admin_client.post(f"/api/apps/{APP}/remove/")

        res = admin_client.post(f"/api/packs/{APP}/apply/")

        assert res.status_code == 200
        assert InstalledApp.objects.get(org=org_a).status == "installed"

    def test_apply_is_still_admin_only(self, user_client):
        assert user_client.post(f"/api/packs/{APP}/apply/").status_code == 403
        assert not InstalledApp.objects.exists()


@pytest.mark.postgres_only
def test_the_table_has_its_policies():
    if connection.vendor != "postgresql":
        pytest.skip("RLS policies exist only on PostgreSQL")
    assert rls_policy_gaps(["installed_app"]) == []


def _need_rls():
    if connection.vendor != "postgresql":
        pytest.skip("Row-level security is a PostgreSQL feature")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )
        if cursor.fetchone()[0]:
            pytest.skip("Needs a role row-level security binds, as in CI")


@pytest.mark.postgres_only
def test_another_orgs_install_row_is_invisible(org_a, org_b, admin_profile, profile_b):
    _need_rls()
    mine = install_app(org_a, APP, admin_profile, sample_data=False)
    with rls_org(org_b):
        theirs = install_app(org_b, "events-weddings", profile_b, sample_data=False)
        assert list(InstalledApp.objects.all()) == [theirs]

    assert list(InstalledApp.objects.all()) == [mine]
