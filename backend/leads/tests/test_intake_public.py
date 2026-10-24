"""`POST /api/public/leads/<intake id>/`, the lead webhook a sender posts to.

Anonymous, so every test posts with no session. The key arrives as
`Authorization: Bearer`, as the preset's own credential (Google Ads'
`google_key`, Tally's `Tally-Signature`), or as `?key=`. The org comes from the
intake id through the unscoped `PortalAccessToken` lookup before any
org-scoped read; the `postgres_only` test at the foot proves that under a role
RLS binds.
"""

import base64
import hashlib
import hmac
import json
import logging
from datetime import timedelta
from unittest import mock

import pytest
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from common.models import Org, PortalAccessToken
from common.public_tokens import redact
from common.testing import set_modules_off
from leads.models import Lead, LeadIntake, LeadIntakeEvent
from leads.views import intake_public_views

KEY = "K3y-for-tests-0123456789abcdefghijklmnopq"
OTHER_KEY = "0ther-org-key-0123456789abcdefghijklmnop"
NOT_FOUND = {"detail": "Not found."}


def url(intake_id, query=""):
    return f"/api/public/leads/{intake_id}/{query}"


def post(client, intake_id, body, *, key=KEY, query="", content_type=None, **headers):
    raw = body if isinstance(body, bytes | str) else json.dumps(body)
    if key is not None:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {key}"
    return client.generic(
        "POST",
        url(intake_id, query),
        raw,
        content_type=content_type or "application/json",
        **headers,
    )


@pytest.fixture(autouse=True)
def _fresh_throttles():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def anon():
    return APIClient()


@pytest.fixture
def intake(org_a):
    return LeadIntake.objects.create(
        org=org_a, name="Site", key=KEY, default_source="web form"
    )


@pytest.fixture
def foreign(org_b):
    return LeadIntake.objects.create(org=org_b, name="Theirs", key=OTHER_KEY)


def events(intake):
    return list(LeadIntakeEvent.objects.filter(intake=intake).order_by("received_at"))


class TestKeys:
    def test_a_bearer_key_creates_and_the_reply_is_only_the_id(
        self, anon, org_a, intake
    ):
        response = post(
            anon, intake.id, {"email": "pat@example.com", "first_name": "Pat"}
        )
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert response.json() == {"result": "created", "lead": str(lead.id)}
        assert (lead.email, lead.first_name, lead.source) == (
            "pat@example.com",
            "Pat",
            "web form",
        )
        assert lead.external_source == f"intake:{intake.id}"

    def test_a_wrong_key_is_401_and_writes_nothing(self, anon, org_a, intake, caplog):
        intake.last_error = "an earlier refusal"
        intake.save()
        caplog.set_level(logging.WARNING, logger="leads.views.intake_public_views")
        response = post(anon, intake.id, {"email": "pat@example.com"}, key="nope-123")
        assert response.status_code == 401
        assert Lead.objects.filter(org=org_a).count() == 0
        assert events(intake) == []
        intake.refresh_from_db()
        assert (intake.last_error, intake.last_received_at) == (
            "an earlier refusal",
            None,
        )
        messages = [r.getMessage() for r in caplog.records]
        assert any(str(intake.id) in m and "Wrong key" in m for m in messages)
        assert not any("nope-123" in m for m in messages)

    def test_no_key_at_all_is_401(self, anon, intake):
        assert post(anon, intake.id, {"email": "a@b.co"}, key=None).status_code == 401

    def test_the_query_key_works(self, anon, org_a, intake):
        response = post(
            anon, intake.id, {"email": "pat@example.com"}, key=None, query=f"?key={KEY}"
        )
        assert response.status_code == 201
        assert (
            post(
                anon,
                intake.id,
                {"email": "sam@example.com"},
                key=None,
                query="?key=bad",
            ).status_code
            == 401
        )

    def test_another_orgs_key_does_not_open_this_intake(
        self, anon, org_a, intake, foreign
    ):
        response = post(anon, intake.id, {"email": "pat@example.com"}, key=OTHER_KEY)
        assert response.status_code == 401
        assert Lead.objects.count() == 0

    def test_a_key_with_characters_outside_ascii_is_a_plain_401(self, anon, intake):
        assert post(anon, intake.id, {"email": "a@b.co"}, key="ключ").status_code == 401

    def test_a_replaced_key_works_for_a_week_then_stops(self, anon, org_a, intake):
        intake.previous_key = KEY
        intake.key = "new-key-0123456789abcdefghijklmnopqrstuv"
        intake.previous_key_expires_at = timezone.now() + timedelta(days=7)
        intake.save()
        assert post(anon, intake.id, {"email": "a@example.com"}).status_code == 201
        assert (
            post(
                anon, intake.id, {"email": "b@example.com"}, key=intake.key
            ).status_code
            == 201
        )
        intake.previous_key_expires_at = timezone.now() - timedelta(seconds=1)
        intake.save()
        assert post(anon, intake.id, {"email": "c@example.com"}).status_code == 401
        assert Lead.objects.filter(org=org_a).count() == 2


class TestNotFound:
    def test_unknown_and_switched_off_answer_the_same(self, anon, org_a, intake):
        unknown = post(
            anon, "6f1c2d3e-4a5b-4c6d-8e7f-901a2b3c4d5e", {"email": "a@b.co"}
        )
        intake.is_active = False
        intake.save()
        off = post(anon, intake.id, {"email": "a@b.co"})
        assert unknown.status_code == off.status_code == 404
        assert unknown.json() == off.json() == NOT_FOUND
        assert Lead.objects.filter(org=org_a).count() == 0

    def test_an_intake_whose_lookup_names_another_org_is_not_found(
        self, anon, org_a, org_b, intake
    ):
        PortalAccessToken.objects.filter(resource_id=intake.id).update(org=org_b)
        response = post(anon, intake.id, {"email": "a@b.co"})
        assert response.status_code == 404
        assert response.json() == NOT_FOUND

    def test_an_id_registered_for_another_resource_is_not_found(self, anon, org_a):
        from common.portal_tokens import register_portal_token

        stray = "0b9c8d7e-6f5a-4b3c-9d2e-1f0a9b8c7d6e"
        register_portal_token(stray, org_a.id, PortalAccessToken.INVOICE, stray)
        assert post(anon, stray, {"email": "a@b.co"}).status_code == 404

    def test_get_is_not_allowed(self, anon, intake):
        assert anon.get(url(intake.id)).status_code == 405


class TestBodies:
    def test_a_body_over_64_kb_is_413(self, anon, org_a, intake):
        body = json.dumps({"email": "a@b.co", "pad": "x" * (65 * 1024)})
        response = post(anon, intake.id, body)
        assert response.status_code == 413
        assert Lead.objects.filter(org=org_a).count() == 0
        assert events(intake)[0].result == "rejected"

    def test_malformed_json_is_400(self, anon, org_a, intake):
        response = post(anon, intake.id, '{"email": ')
        assert response.status_code == 400
        assert Lead.objects.filter(org=org_a).count() == 0
        assert events(intake)[0].result == "rejected"

    @pytest.mark.parametrize(
        "raw", ["[1, 2]", '"text"', "null", '{"a": NaN}', "[" * 2000 + "]" * 2000]
    )
    def test_a_body_that_is_not_an_object_is_400(self, anon, intake, raw):
        assert post(anon, intake.id, raw).status_code == 400

    def test_a_deeply_nested_object_is_400(self, anon, intake):
        nested = "x"
        for _ in range(40):
            nested = {"n": nested}
        assert (
            post(anon, intake.id, {"email": "a@b.co", "deep": nested}).status_code
            == 400
        )

    def test_form_encoded_bodies_work(self, anon, org_a, intake):
        response = post(
            anon,
            intake.id,
            "email=pat%40example.com&first_name=Pat&note=hello",
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert lead.first_name == "Pat"
        assert "note: hello" in lead.description

    def test_another_content_type_is_400(self, anon, intake):
        response = post(anon, intake.id, "<x/>", content_type="application/xml")
        assert response.status_code == 400

    def test_nul_characters_are_dropped_not_stored(self, anon, org_a, intake):
        response = post(
            anon, intake.id, {"email": "pat@example.com", "note": "a\u0000b"}
        )
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert "\x00" not in lead.description
        assert "\x00" not in json.dumps(events(intake)[0].payload)

    def test_an_invalid_value_is_400_with_field_errors_and_logged(
        self, anon, org_a, intake
    ):
        body = {"email": "not-an-email", "phone": "call me maybe", "first_name": "Pat"}
        response = post(anon, intake.id, body)
        assert response.status_code == 400
        errors = response.json()["errors"]
        assert set(errors) == {"email", "phone"}
        assert Lead.objects.filter(org=org_a).count() == 0
        [event] = events(intake)
        assert event.result == "rejected"
        assert event.payload == body

    def test_an_empty_post_is_400(self, anon, intake):
        assert post(anon, intake.id, {}).status_code == 400

    def test_a_mapping_reads_nested_fields_and_keeps_the_rest(
        self, anon, org_a, intake
    ):
        intake.mapping = [
            {"from": "contact.mail", "to": "email"},
            {"from": "contact.name", "to": "first_name"},
        ]
        intake.save()
        response = post(
            anon,
            intake.id,
            {
                "contact": {"mail": "pat@example.com", "name": "Pat"},
                "budget": 5000,
                "status": "converted",
            },
        )
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert (lead.email, lead.first_name, lead.status) == (
            "pat@example.com",
            "Pat",
            "assigned",
        )
        assert "budget: 5000" in lead.description
        assert "status: converted" in lead.description

    def test_a_country_name_becomes_its_code(self, anon, org_a, intake):
        post(anon, intake.id, {"email": "pat@example.com", "country": "united kingdom"})
        assert Lead.objects.get(org=org_a).country == "GB"


class TestOutcomes:
    def test_a_repeat_merges_and_a_retry_is_a_duplicate(self, anon, org_a, intake):
        first = post(anon, intake.id, {"email": "pat@example.com", "external_id": "A1"})
        lead_id = first.json()["lead"]
        again = post(anon, intake.id, {"email": "pat@example.com", "external_id": "A1"})
        assert again.status_code == 200
        assert again.json() == {"result": "duplicate", "lead": lead_id}
        merged = post(anon, intake.id, {"email": "pat@example.com", "message": "hi"})
        assert merged.status_code == 200
        assert merged.json() == {"result": "merged", "lead": lead_id}
        assert [e.result for e in events(intake)] == ["created", "duplicate", "merged"]
        assert events(intake)[0].external_id == "A1"
        assert str(events(intake)[0].lead_id) == lead_id

    def test_settings_shape_the_lead(self, anon, org_a, intake, user_profile):
        from common.models import Tags

        tag = Tags.objects.create(name="Ads", slug="ads", org=org_a)
        intake.tags.add(tag)
        intake.assignee = user_profile
        intake.default_source = "referral"
        intake.source_detail = "Spring fair"
        intake.save()
        post(anon, intake.id, {"email": "pat@example.com"})
        lead = Lead.objects.get(org=org_a)
        assert (lead.source, lead.source_detail) == ("referral", "Spring fair")
        assert list(lead.tags.all()) == [tag]
        assert list(lead.assigned_to.all()) == [user_profile]

    def test_a_success_clears_the_last_error(self, anon, intake):
        post(anon, intake.id, {"email": "a@b.co"}, key="bad")
        post(anon, intake.id, {"email": "pat@example.com"})
        intake.refresh_from_db()
        assert intake.last_error == ""
        assert intake.last_received_at is not None

    def test_events_older_than_thirty_days_are_deleted(self, anon, org_a, intake):
        old = LeadIntakeEvent.objects.create(
            org=org_a,
            intake=intake,
            result="created",
            received_at=timezone.now() - timedelta(days=31),
        )
        recent = LeadIntakeEvent.objects.create(
            org=org_a,
            intake=intake,
            result="created",
            received_at=timezone.now() - timedelta(days=29),
        )
        other = LeadIntake.objects.create(org=org_a, name="Other", key="o" * 40)
        others_old = LeadIntakeEvent.objects.create(
            org=org_a,
            intake=other,
            result="created",
            received_at=timezone.now() - timedelta(days=31),
        )
        post(anon, intake.id, {"email": "pat@example.com"})
        ids = set(LeadIntakeEvent.objects.values_list("id", flat=True))
        assert old.id not in ids
        assert {recent.id, others_old.id} <= ids

    def test_leads_switched_off_is_403_and_logged(self, anon, org_a, intake):
        set_modules_off(org_a, "leads")
        response = post(anon, intake.id, {"email": "pat@example.com"})
        assert response.status_code == 403
        assert response.json() == {
            "detail": "Leads are switched off for this organization."
        }
        assert Lead.objects.filter(org=org_a).count() == 0
        [event] = events(intake)
        assert event.result == "rejected"
        assert "switched off" in event.error

    def test_leads_switched_off_says_nothing_without_the_key(self, anon, org_a, intake):
        set_modules_off(org_a, "leads")
        assert post(anon, intake.id, {"email": "a@b.co"}, key="bad").status_code == 401

    def test_a_failed_save_is_a_5xx_and_logged_with_the_body(
        self, anon, org_a, intake, caplog
    ):
        with mock.patch.object(
            intake_public_views, "receive_lead", side_effect=RuntimeError("db down")
        ):
            response = post(anon, intake.id, {"email": "pat@example.com"})
        assert response.status_code == 500
        assert response.json() == {"detail": "The lead could not be saved. Try again."}
        [event] = events(intake)
        assert (event.result, event.payload) == (
            "rejected",
            {"email": "pat@example.com"},
        )

    def test_a_signed_in_member_of_another_org_gets_no_further(
        self, org_b_client, org_a, intake
    ):
        response = post(org_b_client, intake.id, {"email": "pat@example.com"}, key=None)
        assert response.status_code == 401
        assert Lead.objects.count() == 0


class TestGoogleAds:
    @pytest.fixture
    def ads(self, org_a):
        from leads.intake_presets import default_mapping

        return LeadIntake.objects.create(
            org=org_a,
            name="Ads",
            preset="google_ads",
            key=KEY,
            default_source="google ads",
            mapping=default_mapping("google_ads"),
        )

    def sample(self, key=KEY, **extra):
        body = {
            "lead_id": "TeSter-123-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "user_column_data": [
                {
                    "column_name": "Full Name",
                    "string_value": "Jane Doe",
                    "column_id": "FULL_NAME",
                },
                {"string_value": "jane@example.com", "column_id": "EMAIL"},
                {"string_value": "+16505550123", "column_id": "PHONE_NUMBER"},
                {
                    "column_name": "How soon?",
                    "string_value": "This month",
                    "column_id": "PURCHASE_TIMELINE",
                },
            ],
            "api_version": "1.0",
            "form_id": 40000000000,
            "campaign_id": 20000000000,
            "google_key": key,
            "gcl_id": "gclid-1",
        }
        body.update(extra)
        return body

    def test_a_test_lead_answers_test_and_makes_nothing(self, anon, org_a, ads):
        response = post(anon, ads.id, self.sample(is_test=True), key=None)
        assert response.status_code == 200
        assert response.json() == {"result": "test"}
        assert Lead.objects.filter(org=org_a).count() == 0
        assert events(ads)[0].result == "test"

    def test_a_lead_is_read_from_its_columns(self, anon, org_a, ads):
        response = post(anon, ads.id, self.sample(), key=None)
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert (lead.first_name, lead.email, lead.phone, lead.source) == (
            "Jane Doe",
            "jane@example.com",
            "+16505550123",
            "google ads",
        )
        assert (lead.external_id, lead.source_ref) == (
            "TeSter-123-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "20000000000",
        )
        assert "How soon?: This month" in lead.description
        assert KEY not in lead.description
        assert events(ads)[0].payload["google_key"] == "[Filtered]"

    def test_a_mapping_cannot_copy_the_key_into_the_lead(self, anon, org_a, ads):
        ads.mapping = [{"from": "google_key", "to": "description"}, *ads.mapping]
        ads.save()
        assert post(anon, ads.id, self.sample(), key=None).status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert KEY not in (lead.description or "")
        assert KEY not in json.dumps(events(ads)[0].payload)

    def test_a_wrong_google_key_is_401(self, anon, org_a, ads):
        response = post(anon, ads.id, self.sample(key="wrong"), key=None)
        assert response.status_code == 401
        assert Lead.objects.filter(org=org_a).count() == 0

    def test_google_key_opens_only_a_google_ads_intake(self, anon, org_a, intake):
        response = post(anon, intake.id, self.sample(), key=None)
        assert response.status_code == 401

    def test_a_retried_lead_is_a_duplicate(self, anon, ads):
        post(anon, ads.id, self.sample(), key=None)
        again = post(anon, ads.id, self.sample(), key=None)
        assert again.json()["result"] == "duplicate"


class TestTally:
    @pytest.fixture
    def tally(self, org_a):
        from leads.intake_presets import default_mapping

        return LeadIntake.objects.create(
            org=org_a,
            name="Tally",
            preset="tally",
            key=KEY,
            mapping=default_mapping("tally"),
        )

    def raw(self):
        return json.dumps(
            {
                "eventId": "a4cb511e-d513-4fa5-baee-b815d718dfd1",
                "eventType": "FORM_RESPONSE",
                "createdAt": timezone.now().isoformat(),
                "data": {
                    "responseId": "2wgx4n",
                    "submissionId": "2wgx4n",
                    "respondentId": "dwQKYm",
                    "formId": "VwbNEw",
                    "formName": "Contact",
                    "createdAt": timezone.now().isoformat(),
                    "fields": [
                        {
                            "key": "question_mVGEJz",
                            "label": "First name",
                            "type": "INPUT_TEXT",
                            "value": "Alice",
                        },
                        {
                            "key": "question_3EKz4n",
                            "label": "Your email",
                            "type": "INPUT_EMAIL",
                            "value": "alice@example.com",
                        },
                        {
                            "key": "question_nGJ0V5",
                            "label": "Interested in",
                            "type": "MULTIPLE_CHOICE",
                            "value": ["5c5a"],
                            "options": [
                                {"id": "5c5a", "text": "Buying"},
                                {"id": "x", "text": "Selling"},
                            ],
                        },
                    ],
                },
            },
            separators=(",", ":"),
        )

    def sign(self, raw, key=KEY):
        digest = hmac.new(key.encode(), raw.encode(), hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def test_a_signed_post_creates(self, anon, org_a, tally):
        raw = self.raw()
        response = post(
            anon, tally.id, raw, key=None, HTTP_TALLY_SIGNATURE=self.sign(raw)
        )
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert (lead.first_name, lead.email, lead.external_id, lead.source_ref) == (
            "Alice",
            "alice@example.com",
            "2wgx4n",
            "VwbNEw",
        )
        assert "Interested in: Buying" in lead.description

    def test_a_bad_signature_is_401(self, anon, org_a, tally):
        raw = self.raw()
        response = post(
            anon, tally.id, raw, key=None, HTTP_TALLY_SIGNATURE=self.sign(raw, "wrong")
        )
        assert response.status_code == 401
        assert Lead.objects.filter(org=org_a).count() == 0

    def test_a_signature_over_another_body_is_401(self, anon, org_a, tally):
        raw = self.raw()
        tampered = raw.replace("alice@example.com", "mallory@example.com")
        response = post(
            anon, tally.id, tampered, key=None, HTTP_TALLY_SIGNATURE=self.sign(raw)
        )
        assert response.status_code == 401

    def test_a_tally_signature_does_not_open_a_generic_intake(self, anon, intake):
        raw = self.raw()
        response = post(
            anon, intake.id, raw, key=None, HTTP_TALLY_SIGNATURE=self.sign(raw)
        )
        assert response.status_code == 401


class TestThrottle:
    def test_the_minute_limit_answers_429(self, anon, intake, monkeypatch):
        monkeypatch.setattr(
            intake_public_views.IntakeMinuteThrottle, "rate", "2/min", raising=False
        )
        assert post(anon, intake.id, {"email": "a@example.com"}).status_code == 201
        assert post(anon, intake.id, {"email": "b@example.com"}).status_code == 201
        assert post(anon, intake.id, {"email": "c@example.com"}).status_code == 429

    def test_the_limit_is_per_intake(self, anon, org_a, intake, monkeypatch):
        monkeypatch.setattr(
            intake_public_views.IntakeMinuteThrottle, "rate", "1/min", raising=False
        )
        other = LeadIntake.objects.create(org=org_a, name="Other", key=KEY)
        assert post(anon, intake.id, {"email": "a@example.com"}).status_code == 201
        assert post(anon, other.id, {"email": "b@example.com"}).status_code == 201

    def test_the_day_limit_answers_429(self, anon, intake, monkeypatch):
        monkeypatch.setattr(
            intake_public_views.IntakeDayThrottle, "rate", "1/day", raising=False
        )
        assert post(anon, intake.id, {"email": "a@example.com"}).status_code == 201
        assert post(anon, intake.id, {"email": "b@example.com"}).status_code == 429

    def test_the_rates_are_configured(self):
        from django.conf import settings

        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        assert rates["lead_intake_minute"] == "120/min"
        assert rates["lead_intake_day"] == "5000/day"


class TestKeyStaysOutOfLogs:
    def test_a_bearer_key_is_not_in_the_application_log(self, anon, intake, caplog):
        caplog.set_level(logging.DEBUG)
        post(anon, intake.id, {"email": "pat@example.com"})
        post(anon, intake.id, {"email": "a@b.co"}, key="SECRETVALUE2")
        for record in caplog.records:
            assert KEY not in record.getMessage()
            assert "SECRETVALUE2" not in record.getMessage()

    def test_the_query_key_is_not_in_the_application_log(self, anon, intake, caplog):
        caplog.set_level(logging.DEBUG)
        post(anon, intake.id, {"email": "a@b.co"}, key=None, query="?key=SECRETVALUE1")
        post(
            anon, intake.id, {"email": "pat@example.com"}, key=None, query=f"?key={KEY}"
        )
        for record in caplog.records:
            message = record.getMessage()
            assert "SECRETVALUE1" not in message
            assert KEY not in message

    def test_the_access_log_line_is_redacted(self):
        line = f'"POST /api/public/leads/abc/?x=1&key={KEY}&y=2 HTTP/1.1" 201'
        cleaned = redact(line)
        assert KEY not in cleaned
        assert "key=[Filtered]&y=2" in cleaned
        assert redact("/api/public/leads/abc/?key=") == "/api/public/leads/abc/?key="

    def test_a_sentry_event_drops_the_query_and_body(self):
        from common.sentry_scrub import before_send

        event = {
            "request": {
                "url": "https://api.example.com/api/public/leads/abc/",
                "query_string": f"key={KEY}",
                "data": {"google_key": KEY},
            }
        }
        scrubbed = before_send(event, {})
        assert KEY not in repr(scrubbed)


@pytest.mark.postgres_only
def test_a_post_creates_under_enforced_rls():
    if connection.vendor != "postgresql":
        pytest.skip("RLS requires PostgreSQL")

    def context(value):
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_org', %s, false)", [value])

    org = Org.objects.create(name="RLS Intake Org")
    context(str(org.id))
    try:
        hook = LeadIntake.objects.create(org=org, name="Site", key=KEY)
    finally:
        context("")
    assert not LeadIntake.objects.filter(pk=hook.pk).exists(), (
        "The empty context exposed lead_intake: this role bypasses RLS."
    )

    response = post(APIClient(), hook.id, {"email": "pat@example.com"})

    assert response.status_code == 201, response.content
    context(str(org.id))
    try:
        assert Lead.objects.filter(org=org).count() == 1
        assert (
            LeadIntakeEvent.objects.filter(intake=hook, result="created").count() == 1
        )
    finally:
        context("")


def _from(address):
    return {"REMOTE_ADDR": address}


class TestRefusals:
    def test_wrong_keys_do_not_use_the_webhooks_limit(self, anon, intake, monkeypatch):
        monkeypatch.setattr(
            intake_public_views.IntakeMinuteThrottle, "rate", "2/min", raising=False
        )
        for _ in range(4):
            assert (
                post(anon, intake.id, {"email": "a@b.co"}, key="bad").status_code == 401
            )
        assert post(anon, intake.id, {"email": "pat@example.com"}).status_code == 201

    def test_refusals_are_limited_per_address_and_never_hold_back_the_key(
        self, anon, intake, monkeypatch
    ):
        monkeypatch.setattr(
            intake_public_views.RefusedPostThrottle, "rate", "2/min", raising=False
        )
        here, there = _from("203.0.113.7"), _from("198.51.100.4")
        for _ in range(2):
            assert post(anon, intake.id, {"a": 1}, key="bad", **here).status_code == 401
        refused = post(anon, intake.id, {"a": 1}, key="bad", **here)
        assert refused.status_code == 429
        assert refused["Retry-After"]
        # A shared sender address keeps delivering for the webhooks it holds
        # the key of, and another address is not affected.
        ok = post(anon, intake.id, {"email": "pat@example.com"}, **here)
        assert ok.status_code == 201
        assert post(anon, intake.id, {"a": 1}, key="bad", **there).status_code == 401
        assert [e.result for e in events(intake)] == ["created"]

    def test_unknown_webhooks_count_as_refusals(self, anon, monkeypatch):
        monkeypatch.setattr(
            intake_public_views.RefusedPostThrottle, "rate", "1/min", raising=False
        )
        unknown = "6f1c2d3e-4a5b-4c6d-8e7f-901a2b3c4d5e"
        assert post(anon, unknown, {"a": 1}).status_code == 404
        assert post(anon, unknown, {"a": 1}).status_code == 429

    def test_an_unkeyed_oversized_body_writes_nothing(self, anon, intake):
        body = json.dumps({"pad": "x" * (65 * 1024)})
        assert post(anon, intake.id, body, key="bad").status_code == 413
        assert events(intake) == []

    def test_an_unkeyed_malformed_body_writes_nothing(self, anon, intake):
        assert post(anon, intake.id, '{"email": ', key="bad").status_code == 400
        assert events(intake) == []

    def test_a_keyed_post_over_the_limit_is_a_logged_delivery(
        self, anon, intake, monkeypatch
    ):
        monkeypatch.setattr(
            intake_public_views.IntakeMinuteThrottle, "rate", "1/min", raising=False
        )
        assert post(anon, intake.id, {"email": "a@example.com"}).status_code == 201
        response = post(anon, intake.id, {"email": "b@example.com"})
        assert response.status_code == 429
        assert response["Retry-After"]
        rejected = events(intake)[-1]
        assert (rejected.result, rejected.error, rejected.payload) == (
            "rejected",
            "rate limited",
            {"email": "b@example.com"},
        )
        intake.refresh_from_db()
        assert intake.last_error == "rate limited"


class TestRetries:
    def test_a_retried_merge_is_a_duplicate_with_one_comment_and_one_email(
        self, anon, org_a, intake, django_capture_on_commit_callbacks
    ):
        from django.contrib.contenttypes.models import ContentType

        from common.models import Comment

        # The lead already carries another sender's id, so it cannot take this one.
        lead = Lead.objects.create(
            org=org_a,
            email="pat@example.com",
            external_source="intake:x",
            external_id="X",
        )
        body = {"email": "pat@example.com", "external_id": "A1", "message": "hi"}
        with (
            mock.patch("leads.intake.send_enquired_again_email.delay") as mailed,
            django_capture_on_commit_callbacks(execute=True),
        ):
            first = post(anon, intake.id, body)
            again = post(anon, intake.id, body)
        assert first.json() == {"result": "merged", "lead": str(lead.id)}
        assert again.status_code == 200
        assert again.json() == {"result": "duplicate", "lead": str(lead.id)}
        comments = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(Lead), object_id=lead.id
        )
        assert comments.count() == 1
        assert mailed.call_count == 1
        assert [e.result for e in events(intake)] == ["merged", "duplicate"]

    def test_a_merge_stamps_the_id_on_a_lead_that_had_none(self, anon, org_a, intake):
        lead = Lead.objects.create(org=org_a, email="pat@example.com")
        post(anon, intake.id, {"email": "pat@example.com", "external_id": "A1"})
        lead.refresh_from_db()
        assert (lead.external_source, lead.external_id) == (f"intake:{intake.id}", "A1")

    def test_a_refused_first_post_does_not_make_the_retry_a_duplicate(
        self, anon, org_a, intake
    ):
        bad = post(anon, intake.id, {"email": "nope", "external_id": "A1"})
        assert bad.status_code == 400
        good = post(anon, intake.id, {"email": "pat@example.com", "external_id": "A1"})
        assert good.json()["result"] == "created"


class TestLongValues:
    def test_a_long_value_is_cut_and_kept_whole_in_the_notes(self, anon, org_a, intake):
        name = "N" * 300
        response = post(
            anon, intake.id, {"email": "pat@example.com", "first_name": name}
        )
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert lead.first_name == name[:255]
        assert f"First name: {name}" in lead.description

    def test_a_long_email_is_left_out_and_kept_in_the_notes(self, anon, org_a, intake):
        address = "p" * 250 + "@example.com"
        response = post(anon, intake.id, {"email": address, "first_name": "Pat"})
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert lead.email is None
        assert f"Email: {address}" in lead.description

    def test_a_long_message_is_kept(self, anon, org_a, intake):
        message = "m" * 9000
        response = post(
            anon, intake.id, {"email": "pat@example.com", "description": message}
        )
        assert response.status_code == 201
        assert Lead.objects.get(org=org_a).description == message

    def test_a_long_custom_value_is_cut_and_kept_whole(self, anon, org_a, intake):
        from common.models import CustomFieldDefinition

        CustomFieldDefinition.objects.create(
            org=org_a,
            target_model="Lead",
            key="notes",
            label="Notes",
            field_type="text",
        )
        intake.mapping = [{"from": "notes", "to": "custom_fields.notes"}]
        intake.save()
        value = "v" * 1500
        response = post(anon, intake.id, {"email": "pat@example.com", "notes": value})
        assert response.status_code == 201
        lead = Lead.objects.get(org=org_a)
        assert lead.custom_fields["notes"] == value[:1000]
        assert f"notes: {value}" in lead.description

    @pytest.mark.parametrize(
        "query",
        [
            "?KEY=SECRET1",
            "?Key=SECRET1",
            "?x=1&%6Bey=SECRET1",
            "?%6b%65%79=SECRET1&y=2",
            "?key=SECRET1&key=SECRET1",
        ],
    )
    def test_the_key_is_cut_from_logs_however_it_is_written(self, query):
        cleaned = redact(f"/api/public/leads/abc/{query}")
        assert "SECRET1" not in cleaned
        assert "[Filtered]" in cleaned

    def test_other_parameters_are_left_alone(self):
        assert redact("/api/public/leads/abc/?monkey=1&keys=2") == (
            "/api/public/leads/abc/?monkey=1&keys=2"
        )


class TestWebForms:
    def test_a_phone_only_match_does_not_take_the_forms_email(self, anon, org_a):
        from django.contrib.contenttypes.models import ContentType

        from common.models import Comment
        from webforms.models import WebForm, WebFormField

        org_a.default_country = "US"
        org_a.save(update_fields=["default_country"])
        form = WebForm.objects.create(name="Contact", org=org_a, is_published=True)
        for order, field in enumerate(["email", "phone"]):
            WebFormField.objects.create(
                form=form,
                org=org_a,
                order=order,
                source=WebFormField.SOURCE_LEAD,
                lead_field=field,
                label=field,
            )
        lead = Lead.objects.create(org=org_a, phone="+1 (555) 123-4567")

        response = anon.post(
            f"/api/public/forms/{org_a.id}/{form.id}/submit/",
            {"email": "pat@example.com", "phone": "555-123-4567"},
            format="json",
        )

        assert response.status_code == 200
        assert Lead.objects.filter(org=org_a).count() == 1
        lead.refresh_from_db()
        assert lead.email is None
        comment = Comment.objects.get(
            content_type=ContentType.objects.get_for_model(Lead), object_id=lead.id
        )
        assert "Email: pat@example.com" in comment.comment


@pytest.mark.postgres_only
@pytest.mark.django_db(transaction=True)
def test_two_posts_with_one_id_at_once_merge_once(org_a):
    """Both posts start together and both match the lead by email. The second
    waits on the intake row's lock, then finds the first's delivery and
    answers duplicate. Without the lock both merged (two comments): the lead
    already holds another sender's id, so the lead row cannot tell them apart."""
    import threading

    from django.contrib.contenttypes.models import ContentType

    from common.models import Comment
    from common.tasks import set_rls_context

    if connection.vendor != "postgresql":
        pytest.skip("row locks need PostgreSQL")

    hook = LeadIntake.objects.create(org=org_a, name="Site", key=KEY)
    lead = Lead.objects.create(
        org=org_a, email="pat@example.com", external_source="intake:x", external_id="X"
    )
    body = {"email": "pat@example.com", "external_id": "A1", "message": "hi"}
    barrier = threading.Barrier(2)
    answers, errors = [], []

    def worker():
        try:
            barrier.wait()
            answers.append(post(APIClient(), hook.id, body).json()["result"])
        except Exception as exc:  # recorded and asserted on below
            errors.append(exc)
        finally:
            connection.close()

    with mock.patch("leads.intake.send_enquired_again_email.delay"):
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

    assert errors == []
    assert sorted(answers) == ["duplicate", "merged"]
    set_rls_context(org_a.id)
    comments = Comment.objects.filter(
        content_type=ContentType.objects.get_for_model(Lead), object_id=lead.id
    )
    assert comments.count() == 1
    assert Lead.objects.filter(org=org_a).count() == 1
