"""The lead webhook settings API: `/api/leads/intakes/`, admins only.

Every refusal is paired with the admin call that succeeds, so a check that
refuses everybody fails here too.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from common.models import CustomFieldDefinition, PortalAccessToken, Profile, Tags, User
from common.portal_tokens import resolve_portal_org
from common.testing import set_modules_off
from leads.models import Lead, LeadIntake, LeadIntakeEvent, LeadSource

URL = "/api/leads/intakes/"


def detail(intake_id, tail=""):
    return f"{URL}{intake_id}/{tail}"


@pytest.fixture
def intake(org_a):
    return LeadIntake.objects.create(
        org=org_a, name="Ads", preset="google_ads", key="k" * 43
    )


@pytest.fixture
def foreign(org_b):
    return LeadIntake.objects.create(org=org_b, name="Theirs", key="t" * 43)


class TestWhoMayUseIt:
    def test_a_member_is_refused_the_list_and_an_admin_is_not(
        self, user_client, admin_client, intake
    ):
        assert user_client.get(URL).status_code == 403
        response = admin_client.get(URL)
        assert response.status_code == 200
        assert [row["id"] for row in response.json()["intakes"]] == [str(intake.id)]

    def test_a_member_cannot_create_and_an_admin_can(self, user_client, admin_client):
        assert user_client.post(URL, {"name": "Mine"}, format="json").status_code == 403
        assert LeadIntake.objects.count() == 0
        assert (
            admin_client.post(URL, {"name": "Mine"}, format="json").status_code == 201
        )

    @pytest.mark.parametrize(
        "method,tail",
        [
            ("get", ""),
            ("patch", ""),
            ("delete", ""),
            ("post", "key/"),
            ("get", "deliveries/"),
            ("post", "test/"),
        ],
    )
    def test_a_member_is_refused_every_detail_route(
        self, user_client, intake, method, tail
    ):
        response = getattr(user_client, method)(detail(intake.id, tail), format="json")
        assert response.status_code == 403
        intake.refresh_from_db()
        assert intake.key == "k" * 43
        assert LeadIntake.objects.filter(pk=intake.pk).exists()

    @pytest.mark.parametrize(
        "method,tail",
        [
            ("get", ""),
            ("patch", ""),
            ("delete", ""),
            ("post", "key/"),
            ("get", "deliveries/"),
            ("post", "test/"),
        ],
    )
    def test_another_orgs_intake_is_not_found(
        self, admin_client, foreign, method, tail
    ):
        response = getattr(admin_client, method)(
            detail(foreign.id, tail), {"name": "Mine"}, format="json"
        )
        assert response.status_code == 404
        foreign.refresh_from_db()
        assert (foreign.name, foreign.key) == ("Theirs", "t" * 43)
        assert not LeadIntakeEvent.objects.filter(intake=foreign).exists()

    def test_the_list_holds_only_this_orgs_intakes(self, admin_client, intake, foreign):
        ids = [row["id"] for row in admin_client.get(URL).json()["intakes"]]
        assert ids == [str(intake.id)]

    def test_leads_switched_off_hides_the_routes(self, admin_client, org_a, intake):
        set_modules_off(org_a, "leads")
        response = admin_client.get(URL)
        assert response.status_code == 404
        assert response.json()["code"] == "module_off"


class TestCreate:
    def test_the_key_is_answered_once(self, admin_client, org_a):
        response = admin_client.post(
            URL, {"name": "Google", "preset": "google_ads"}, format="json"
        )
        assert response.status_code == 201
        body = response.json()
        intake = LeadIntake.objects.get(pk=body["id"])
        assert body["key"] == intake.key
        assert len(intake.key) >= 32
        assert body["key_hint"] == intake.key[-4:]
        assert body["url"] == f"https://api.example.com/api/public/leads/{intake.id}/"

        again = admin_client.get(detail(intake.id)).json()
        assert "key" not in again
        assert again["key_hint"] == intake.key[-4:]
        listed = admin_client.get(URL).json()["intakes"][0]
        assert "key" not in listed
        assert intake.key not in str(listed)

    def test_the_answer_has_the_contract_fields(self, admin_client):
        body = admin_client.post(URL, {"name": "Any"}, format="json").json()
        assert set(body) >= {
            "id",
            "name",
            "preset",
            "url",
            "key_hint",
            "key",
            "mapping",
            "default_source",
            "source_detail",
            "tags",
            "assignee",
            "is_active",
            "last_received_at",
            "last_error",
            "created_at",
        }
        assert body["preset"] == "generic"
        assert body["mapping"] == []
        assert body["default_source"] == "web form"
        assert body["is_active"] is True

    def test_a_preset_starts_with_its_mapping_and_source(self, admin_client):
        body = admin_client.post(
            URL, {"name": "Ads", "preset": "google_ads"}, format="json"
        ).json()
        assert {"from": "user_column_data.EMAIL", "to": "email"} in body["mapping"]
        assert body["default_source"] == "google ads"

    def test_the_url_id_resolves_to_the_org_without_rls(self, admin_client, org_a):
        body = admin_client.post(URL, {"name": "Any"}, format="json").json()
        assert resolve_portal_org(body["id"], PortalAccessToken.LEAD_INTAKE) == str(
            org_a.id
        )

    def test_server_owned_fields_in_the_body_are_ignored(
        self, admin_client, org_a, org_b
    ):
        response = admin_client.post(
            URL,
            {
                "name": "Any",
                "key": "chosen-by-the-caller-000000000000000",
                "previous_key": "x",
                "org": str(org_b.id),
                "last_received_at": "2026-01-01T00:00:00Z",
                "last_error": "planted",
                "url": "https://evil.example/",
                "id": "6f1c2d3e-4a5b-4c6d-8e7f-901a2b3c4d5e",
            },
            format="json",
        )
        assert response.status_code == 201
        intake = LeadIntake.objects.get(pk=response.json()["id"])
        assert intake.org_id == org_a.id
        assert intake.key != "chosen-by-the-caller-000000000000000"
        assert intake.previous_key == ""
        assert intake.last_received_at is None
        assert intake.last_error == ""
        assert str(intake.id) != "6f1c2d3e-4a5b-4c6d-8e7f-901a2b3c4d5e"

    def test_a_name_is_required(self, admin_client):
        assert admin_client.post(URL, {}, format="json").status_code == 400
        assert admin_client.post(URL, {"name": "  "}, format="json").status_code == 400

    def test_an_unknown_preset_is_refused(self, admin_client):
        response = admin_client.post(
            URL, {"name": "x", "preset": "zapier"}, format="json"
        )
        assert response.status_code == 400


class TestMapping:
    def _create(self, client, mapping):
        return client.post(URL, {"name": "x", "mapping": mapping}, format="json")

    def test_a_whitelisted_column_is_accepted(self, admin_client):
        response = self._create(admin_client, [{"from": "contact.mail", "to": "email"}])
        assert response.status_code == 201
        assert response.json()["mapping"] == [{"from": "contact.mail", "to": "email"}]

    @pytest.mark.parametrize(
        "target", ["status", "org", "assigned_to", "is_sample", "created_by", ""]
    )
    def test_a_column_outside_the_whitelist_is_refused(self, admin_client, target):
        response = self._create(admin_client, [{"from": "a", "to": target}])
        assert response.status_code == 400
        assert LeadIntake.objects.count() == 0

    def test_a_custom_field_of_this_org_is_accepted_and_others_refused(
        self, admin_client, org_a, org_b
    ):
        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Lead",
            key="budget",
            label="Budget",
            field_type="text",
        )
        CustomFieldDefinition.objects.create(
            org=org_b, target_model="Lead", key="secret", label="S", field_type="text"
        )
        CustomFieldDefinition.objects.create(
            org=org_a, target_model="Contact", key="ctc", label="C", field_type="text"
        )
        ok = self._create(admin_client, [{"from": "b", "to": "custom_fields.budget"}])
        assert ok.status_code == 201
        for target in ("custom_fields.secret", "custom_fields.ctc", "custom_fields."):
            response = self._create(admin_client, [{"from": "b", "to": target}])
            assert response.status_code == 400, target

    def test_a_stored_custom_target_survives_its_field_being_switched_off(
        self, admin_client, org_a
    ):
        field = CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Lead",
            key="budget",
            label="Budget",
            field_type="text",
        )
        intake_id = self._create(
            admin_client, [{"from": "b", "to": "custom_fields.budget"}]
        ).json()["id"]
        field.is_active = False
        field.save()
        response = admin_client.patch(
            detail(intake_id),
            {"mapping": [{"from": "b", "to": "custom_fields.budget"}]},
            format="json",
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "mapping",
        [
            "email",
            [["a", "email"]],
            [{"to": "email"}],
            [{"from": "", "to": "email"}],
            [{"from": "x" * 256, "to": "email"}],
            [{"from": 7, "to": "email"}],
            [{"from": "a", "to": "email"}] * 51,
        ],
    )
    def test_malformed_mappings_are_refused(self, admin_client, mapping):
        assert self._create(admin_client, mapping).status_code == 400


class TestSettings:
    def test_an_unknown_source_is_refused(self, admin_client):
        response = admin_client.post(
            URL, {"name": "x", "default_source": "tv"}, format="json"
        )
        assert response.status_code == 400

    def test_a_retired_stored_source_survives_a_save(self, admin_client, org_a, intake):
        LeadSource.objects.create(
            org=org_a, key="old fair", label="Old", is_active=False
        )
        intake.default_source = "old fair"
        intake.save()
        response = admin_client.patch(
            detail(intake.id),
            {"default_source": "old fair", "name": "Renamed"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["default_source"] == "old fair"

    def test_an_empty_source_is_allowed(self, admin_client):
        response = admin_client.post(
            URL, {"name": "x", "default_source": ""}, format="json"
        )
        assert response.status_code == 201
        assert response.json()["default_source"] == ""

    def test_tags_and_assignee_of_this_org(self, admin_client, org_a, user_profile):
        tag = Tags.objects.create(name="Ads", slug="ads", org=org_a)
        response = admin_client.post(
            URL,
            {"name": "x", "tags": [str(tag.id)], "assignee": str(user_profile.id)},
            format="json",
        )
        assert response.status_code == 201
        body = response.json()
        assert body["tags"] == [str(tag.id)]
        assert body["assignee"] == str(user_profile.id)
        assert body["assignee_details"]["is_active"] is True

    def test_another_orgs_tag_or_member_is_refused(
        self, admin_client, org_b, profile_b
    ):
        tag = Tags.objects.create(name="Theirs", slug="theirs", org=org_b)
        assert (
            admin_client.post(
                URL, {"name": "x", "tags": [str(tag.id)]}, format="json"
            ).status_code
            == 400
        )
        assert (
            admin_client.post(
                URL, {"name": "x", "assignee": str(profile_b.id)}, format="json"
            ).status_code
            == 400
        )
        assert LeadIntake.objects.count() == 0

    def test_a_deactivated_member_cannot_be_chosen_but_is_kept(
        self, admin_client, org_a, intake
    ):
        user = User.objects.create_user(email="gone@test.com", password="x")
        gone = Profile.objects.create(
            user=user, org=org_a, role="USER", is_active=False
        )
        refused = admin_client.patch(
            detail(intake.id), {"assignee": str(gone.id)}, format="json"
        )
        assert refused.status_code == 400
        intake.assignee = gone
        intake.save()
        kept = admin_client.patch(
            detail(intake.id), {"assignee": str(gone.id), "name": "n"}, format="json"
        )
        assert kept.status_code == 200

    def test_patch_switches_off_and_renames(self, admin_client, intake):
        response = admin_client.patch(
            detail(intake.id), {"is_active": False, "name": "Paused"}, format="json"
        )
        assert response.status_code == 200
        intake.refresh_from_db()
        assert (intake.is_active, intake.name) == (False, "Paused")

    def test_patch_cannot_write_the_key(self, admin_client, intake):
        admin_client.patch(detail(intake.id), {"key": "mine" * 10}, format="json")
        intake.refresh_from_db()
        assert intake.key == "k" * 43

    def test_delete_removes_the_intake_and_its_url(self, admin_client, intake):
        assert resolve_portal_org(str(intake.id), PortalAccessToken.LEAD_INTAKE)
        response = admin_client.delete(detail(intake.id))
        assert response.status_code == 204
        assert not LeadIntake.objects.filter(pk=intake.pk).exists()
        assert resolve_portal_org(str(intake.id), PortalAccessToken.LEAD_INTAKE) is None


class TestReplaceKey:
    def test_answers_a_new_key_and_keeps_the_old_one_for_a_week(
        self, admin_client, intake
    ):
        response = admin_client.post(detail(intake.id, "key/"))
        assert response.status_code == 200
        new = response.json()["key"]
        intake.refresh_from_db()
        assert new == intake.key != "k" * 43
        assert intake.previous_key == "k" * 43
        week = timezone.now() + timedelta(days=7)
        assert abs(intake.previous_key_expires_at - week) < timedelta(minutes=1)
        assert response.json()["key_hint"] == new[-4:]
        assert "key" not in admin_client.get(detail(intake.id)).json()


class TestDeliveries:
    def test_newest_first_and_at_most_fifty(self, admin_client, org_a, intake):
        now = timezone.now()
        lead = Lead.objects.create(org=org_a, email="pat@example.com")
        for minutes in range(55):
            LeadIntakeEvent.objects.create(
                org=org_a,
                intake=intake,
                received_at=now - timedelta(minutes=minutes),
                result="created",
                lead=lead,
                external_id=f"e{minutes}",
                payload={"secret": "kept out of the answer"},
            )
        response = admin_client.get(detail(intake.id, "deliveries/"))
        assert response.status_code == 200
        rows = response.json()["deliveries"]
        assert len(rows) == 50
        assert [row["external_id"] for row in rows[:2]] == ["e0", "e1"]
        assert set(rows[0]) == {
            "id",
            "received_at",
            "result",
            "lead",
            "external_id",
            "error",
        }
        assert rows[0]["lead"] == str(lead.id)

    def test_only_this_intakes_deliveries(self, admin_client, org_a, intake):
        other = LeadIntake.objects.create(org=org_a, name="Other", key="o" * 40)
        LeadIntakeEvent.objects.create(org=org_a, intake=other, result="rejected")
        assert admin_client.get(detail(intake.id, "deliveries/")).json() == {
            "deliveries": []
        }


class TestOldDeliveriesGo:
    """Deliveries hold the posted body, so after 30 days they go when an admin
    reads the webhook, even one that nobody posts to any more."""

    @staticmethod
    def _aged(org, intake, days):
        return LeadIntakeEvent.objects.create(
            org=org,
            intake=intake,
            result="created",
            received_at=timezone.now() - timedelta(days=days),
            payload={"email": "pat@example.com"},
        )

    @pytest.mark.parametrize("tail", ["", "deliveries/"])
    def test_an_admin_read_deletes_this_webhooks_old_deliveries(
        self, admin_client, org_a, intake, tail
    ):
        old, recent = self._aged(org_a, intake, 31), self._aged(org_a, intake, 29)
        other = LeadIntake.objects.create(org=org_a, name="Other", key="o" * 40)
        others_old = self._aged(org_a, other, 31)

        assert admin_client.get(detail(intake.id, tail)).status_code == 200

        ids = set(LeadIntakeEvent.objects.values_list("id", flat=True))
        assert old.id not in ids
        assert {recent.id, others_old.id} <= ids

    def test_the_list_answered_holds_no_old_delivery(self, admin_client, org_a, intake):
        self._aged(org_a, intake, 31)
        recent = self._aged(org_a, intake, 29)
        rows = admin_client.get(detail(intake.id, "deliveries/")).json()["deliveries"]
        assert [row["id"] for row in rows] == [str(recent.id)]

    @pytest.mark.parametrize("tail", ["", "deliveries/"])
    def test_a_refused_member_deletes_nothing(self, user_client, org_a, intake, tail):
        old = self._aged(org_a, intake, 31)
        assert user_client.get(detail(intake.id, tail)).status_code == 403
        assert LeadIntakeEvent.objects.filter(pk=old.pk).exists()


class TestSendATest:
    def test_logs_a_test_delivery_and_makes_no_lead(self, admin_client, org_a, intake):
        response = admin_client.post(detail(intake.id, "test/"))
        assert response.status_code == 201
        event = LeadIntakeEvent.objects.get(intake=intake)
        assert (event.result, event.lead) == ("test", None)
        assert response.json()["delivery"]["result"] == "test"
        assert Lead.objects.filter(org=org_a).count() == 0

    def test_refused_while_switched_off(self, admin_client, intake):
        intake.is_active = False
        intake.save()
        response = admin_client.post(detail(intake.id, "test/"))
        assert response.status_code == 400
        assert not LeadIntakeEvent.objects.filter(intake=intake).exists()
