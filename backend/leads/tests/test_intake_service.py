"""`leads.intake.receive_lead`, the one way a lead arrives from outside.

Matching runs external id, then email, then exact `phone_e164`, against leads
of any status. Every outcome is pinned both ways where it is a decision: a
merge that should happen and one that should not, an email that is sent and
one that is not.
"""

from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.utils import timezone

from automation.models import AutomationRule
from common.models import Comment, CustomFieldDefinition, Profile, Tags, User
from contacts.models import Contact
from interactions.models import Interaction
from leads import intake
from leads.intake import IncomingLead, IntakeResult, receive_lead
from leads.models import Lead, LeadPipeline, LeadSource, LeadStage

SOURCE = "intake:11111111-1111-4111-8111-111111111111"


def comments_on(record):
    return Comment.objects.filter(
        content_type=ContentType.objects.get_for_model(type(record)),
        object_id=record.id,
    )


def enquiries_on(record):
    """The enquiries homed on `record`, oldest first."""
    home = "lead" if isinstance(record, Lead) else "contact"
    return Interaction.objects.filter(
        kind="enquiry", home=home, **{home: record}
    ).order_by("created_at")


def incoming(**overrides):
    fields = {
        "values": {"first_name": "Pat", "email": "pat@example.com"},
        "custom_fields": {},
        "source": "google ads",
        "external_source": SOURCE,
        "channel_label": "webhook Ads",
    }
    fields.update(overrides)
    return IncomingLead(**fields)


@pytest.fixture
def us_org(org_a):
    org_a.default_country = "US"
    org_a.save(update_fields=["default_country"])
    return org_a


@pytest.fixture
def member(org_a):
    user = User.objects.create_user(email="owner@test.com", password="x")
    return Profile.objects.create(user=user, org=org_a, role="USER", is_active=True)


@pytest.fixture
def sent(monkeypatch):
    """Every notification task queued, as (task name, args, kwargs)."""
    calls = []

    def record(name):
        return lambda *args, **kwargs: calls.append((name, args, kwargs))

    monkeypatch.setattr(
        intake.send_enquired_again_email, "delay", record("enquired_again")
    )
    monkeypatch.setattr(intake.send_email_to_assigned_user, "delay", record("assigned"))
    return calls


@pytest.fixture
def processed():
    """Every change handed to the automation engine."""
    received = []
    with mock.patch("automation.engine.process", side_effect=received.extend):
        yield received


def run(org, data, capture):
    with capture(execute=True):
        return receive_lead(org, data)


class TestCreate:
    def test_creates_a_lead_with_what_arrived(
        self, org_a, member, django_capture_on_commit_callbacks
    ):
        tag = Tags.objects.create(name="Ads", slug="ads", org=org_a)
        result = run(
            org_a,
            incoming(
                values={
                    "first_name": "Pat",
                    "email": "pat@example.com",
                    "company_name": "Acme",
                },
                source_detail="Spring",
                source_ref="cmp-9",
                external_id="L-1",
                tags=(tag,),
                assignee=member,
                enquiry_text="Wants a quote",
            ),
            django_capture_on_commit_callbacks,
        )

        assert result.result == "created"
        assert result.contact is None
        lead = Lead.objects.get(pk=result.lead.pk)
        assert lead.org_id == org_a.id
        assert (lead.first_name, lead.email, lead.company_name) == (
            "Pat",
            "pat@example.com",
            "Acme",
        )
        assert (lead.source, lead.source_detail, lead.source_ref) == (
            "google ads",
            "Spring",
            "cmp-9",
        )
        assert (lead.external_source, lead.external_id) == (SOURCE, "L-1")
        assert lead.status == "assigned"
        assert lead.description == "Wants a quote"
        assert lead.last_enquiry_at is not None
        assert list(lead.tags.all()) == [tag]
        assert list(lead.assigned_to.all()) == [member]
        assert lead.created_by_id == member.user_id
        # The arrival is an enquiry on the timeline, not a comment.
        assert comments_on(lead).count() == 0
        assert enquiries_on(lead).get().body == "Wants a quote"

    def test_a_mapped_description_keeps_the_text_on_the_enquiry(
        self, org_a, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a,
            incoming(
                values={"email": "pat@example.com", "description": "Hello"},
                enquiry_text="Budget: 5000",
            ),
            django_capture_on_commit_callbacks,
        )
        assert result.lead.description == "Hello"
        assert enquiries_on(result.lead).get().body == "Budget: 5000"
        assert comments_on(result.lead).count() == 0

    def test_only_whitelisted_columns_are_written(
        self, org_a, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a,
            incoming(
                values={
                    "email": "pat@example.com",
                    "status": "converted",
                    "org_id": "x",
                    "is_sample": True,
                    "opportunity_amount": 9,
                }
            ),
            django_capture_on_commit_callbacks,
        )
        lead = Lead.objects.get(pk=result.lead.pk)
        assert lead.status == "assigned"
        assert lead.is_sample is False
        assert lead.opportunity_amount is None

    def test_an_unknown_source_falls_back_to_other(
        self, org_a, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a, incoming(source="tv advert"), django_capture_on_commit_callbacks
        )
        assert result.lead.source == "other"

    def test_a_retired_source_is_kept(self, org_a, django_capture_on_commit_callbacks):
        LeadSource.objects.create(
            org=org_a, key="google ads", label="Google ads", is_active=False
        )
        result = run(org_a, incoming(), django_capture_on_commit_callbacks)
        assert result.lead.source == "google ads"

    def test_no_source_stays_empty(self, org_a, django_capture_on_commit_callbacks):
        result = run(org_a, incoming(source=""), django_capture_on_commit_callbacks)
        assert result.lead.source == ""

    def test_an_inactive_or_foreign_assignee_is_nobody(
        self, org_a, member, profile_b, django_capture_on_commit_callbacks
    ):
        member.is_active = False
        member.save(update_fields=["is_active"])
        first = run(
            org_a, incoming(assignee=member), django_capture_on_commit_callbacks
        )
        second = run(
            org_a,
            incoming(values={"email": "b@example.com"}, assignee=profile_b),
            django_capture_on_commit_callbacks,
        )
        assert first.lead.assigned_to.count() == 0
        assert second.lead.assigned_to.count() == 0
        assert first.lead.created_by_id is None

    def test_the_assignee_is_told(
        self, org_a, member, sent, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a, incoming(assignee=member), django_capture_on_commit_callbacks
        )
        assert sent == [
            (
                "assigned",
                ([str(member.id)], str(result.lead.id), str(org_a.id)),
                {"source": "webhook Ads"},
            )
        ]

    def test_nobody_is_told_when_nobody_is_assigned(
        self, org_a, sent, django_capture_on_commit_callbacks
    ):
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        assert sent == []


class TestMergeByEmail:
    @pytest.fixture
    def lead(self, org_a, member):
        lead = Lead.objects.create(
            org=org_a,
            first_name="Pat",
            email="Pat@Example.com",
            status="in process",
            source="call",
        )
        lead.assigned_to.add(member)
        return lead

    def test_fills_blanks_only_and_records_the_enquiry(
        self, org_a, lead, django_capture_on_commit_callbacks
    ):
        tag = Tags.objects.create(name="Ads", slug="ads", org=org_a)
        result = run(
            org_a,
            incoming(
                values={
                    "first_name": "Impostor",
                    "email": " PAT@example.com ",
                    "company_name": "Acme",
                },
                custom_fields={},
                enquiry_text="Second ask",
                tags=(tag,),
            ),
            django_capture_on_commit_callbacks,
        )

        assert isinstance(result, IntakeResult)
        assert (result.result, result.lead.pk, result.contact) == (
            "merged",
            lead.pk,
            None,
        )
        lead.refresh_from_db()
        assert lead.first_name == "Pat"
        assert lead.company_name == "Acme"
        assert lead.status == "in process"
        assert lead.source == "call"
        assert lead.last_enquiry_at is not None
        assert list(lead.tags.all()) == [tag]
        enquiry = enquiries_on(lead).get()
        assert enquiry.body == "Second ask"
        assert enquiry.subject == "webhook Ads"
        assert enquiry.logged_by is None
        assert comments_on(lead).count() == 0
        assert Lead.objects.filter(org=org_a).count() == 1

    def test_emails_the_active_assignees(
        self, org_a, lead, sent, django_capture_on_commit_callbacks
    ):
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        assert sent == [
            (
                "enquired_again",
                (str(org_a.id),),
                {
                    "lead_id": str(lead.id),
                    "contact_id": None,
                    "channel_label": "webhook Ads",
                },
            )
        ]

    def test_a_blank_custom_field_is_filled_and_a_set_one_kept(
        self, org_a, lead, django_capture_on_commit_callbacks
    ):
        for key in ("budget", "notes"):
            CustomFieldDefinition.objects.create(
                org=org_a, target_model="Lead", key=key, label=key, field_type="text"
            )
        lead.custom_fields = {"budget": "100"}
        lead.save()
        run(
            org_a,
            incoming(custom_fields={"budget": "1", "notes": "hi"}),
            django_capture_on_commit_callbacks,
        )
        lead.refresh_from_db()
        assert lead.custom_fields == {"budget": "100", "notes": "hi"}

    def test_a_lead_in_another_org_is_never_matched(
        self, org_a, org_b, django_capture_on_commit_callbacks
    ):
        other = Lead.objects.create(org=org_b, email="pat@example.com")
        result = run(org_a, incoming(), django_capture_on_commit_callbacks)
        assert result.result == "created"
        assert result.lead.pk != other.pk
        assert result.lead.org_id == org_a.id

    def test_the_lead_takes_the_external_id_when_it_had_none(
        self, org_a, lead, django_capture_on_commit_callbacks
    ):
        run(org_a, incoming(external_id="G-7"), django_capture_on_commit_callbacks)
        lead.refresh_from_db()
        assert (lead.external_source, lead.external_id) == (SOURCE, "G-7")
        again = run(
            org_a, incoming(external_id="G-7"), django_capture_on_commit_callbacks
        )
        assert again.result == "duplicate"

    def test_an_external_id_already_on_the_lead_is_kept(
        self, org_a, lead, django_capture_on_commit_callbacks
    ):
        lead.external_source, lead.external_id = "intake:other", "X-1"
        lead.save()
        run(org_a, incoming(external_id="G-7"), django_capture_on_commit_callbacks)
        lead.refresh_from_db()
        assert (lead.external_source, lead.external_id) == ("intake:other", "X-1")

    def test_a_merge_with_no_text_is_an_empty_enquiry_and_no_comment(
        self, org_a, lead, django_capture_on_commit_callbacks
    ):
        run(org_a, incoming(enquiry_text=""), django_capture_on_commit_callbacks)
        assert comments_on(lead).count() == 0
        assert enquiries_on(lead).get().body == ""

    def test_a_long_enquiry_is_cut_to_fit(
        self, org_a, lead, django_capture_on_commit_callbacks
    ):
        run(
            org_a,
            incoming(enquiry_text="x" * 30_000),
            django_capture_on_commit_callbacks,
        )
        assert len(enquiries_on(lead).get().body) <= 10_000


class TestMergeByPhone:
    def test_matches_the_same_number_written_another_way(
        self, us_org, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(org=us_org, phone="+1 (555) 123-4567")
        result = run(
            us_org,
            incoming(
                values={
                    "phone": "555-123-4567",
                    "first_name": "Pat",
                    "email": "pat@example.com",
                }
            ),
            django_capture_on_commit_callbacks,
        )
        assert result.result == "merged"
        assert result.lead.pk == lead.pk
        lead.refresh_from_db()
        assert lead.first_name == "Pat"
        # A number alone does not make the sender this person's mailbox.
        assert lead.email is None
        assert "Email: pat@example.com" in enquiries_on(lead).get().body

    def test_a_different_number_creates(
        self, us_org, django_capture_on_commit_callbacks
    ):
        Lead.objects.create(org=us_org, phone="+1 (555) 123-4567")
        result = run(
            us_org,
            incoming(values={"phone": "555-123-9999"}),
            django_capture_on_commit_callbacks,
        )
        assert result.result == "created"

    def test_a_number_with_no_e164_value_never_merges(
        self, org_a, django_capture_on_commit_callbacks
    ):
        """No country, so a local number has no E.164 form. The loose
        last-ten-digits rule only suggests duplicates; it never merges."""
        Lead.objects.create(org=org_a, phone="555-123-4567")
        result = run(
            org_a,
            incoming(values={"phone": "(555) 123-4567"}),
            django_capture_on_commit_callbacks,
        )
        assert result.result == "created"
        assert Lead.objects.filter(org=org_a).count() == 2

    def test_an_email_another_lead_holds_is_not_copied(
        self, us_org, django_capture_on_commit_callbacks
    ):
        by_phone = Lead.objects.create(org=us_org, phone="+1 555 123 4567")
        holder = Lead.objects.create(org=us_org, email="pat@example.com")
        # The email lookup misses (another arrival took the address between
        # the lookups), so the phone decides the match.
        with mock.patch.object(intake, "_match_email", return_value=None):
            result = run(
                us_org,
                incoming(values={"phone": "555-123-4567", "email": "pat@example.com"}),
                django_capture_on_commit_callbacks,
            )
        assert result.result == "merged"
        assert result.lead.pk == by_phone.pk
        by_phone.refresh_from_db()
        assert by_phone.email is None
        holder.refresh_from_db()
        assert holder.email == "pat@example.com"

    def test_an_external_id_match_does_not_take_anothers_email(
        self, org_a, django_capture_on_commit_callbacks
    ):
        mine = Lead.objects.create(
            org=org_a, external_source=SOURCE, external_id="L-1", first_name="Pat"
        )
        Lead.objects.create(org=org_a, email="pat@example.com")
        result = run(
            org_a, incoming(external_id="L-1"), django_capture_on_commit_callbacks
        )
        assert result.result == "duplicate"
        mine.refresh_from_db()
        assert mine.email is None


class TestStatuses:
    def test_a_closed_lead_comes_back_as_recycled(
        self, org_a, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(org=org_a, email="pat@example.com", status="closed")
        result = run(org_a, incoming(), django_capture_on_commit_callbacks)
        assert result.result == "merged"
        lead.refresh_from_db()
        assert lead.status == "recycled"

    def test_an_open_lead_keeps_its_status(
        self, org_a, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a, email="pat@example.com", status="assigned"
        )
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        lead.refresh_from_db()
        assert lead.status == "assigned"

    def test_a_converted_lead_records_the_enquiry_on_its_contact(
        self, org_a, member, sent, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a, email="pat@example.com", status="converted", first_name="Pat"
        )
        contact = Contact.objects.create(
            org=org_a, first_name="Pat", last_name="P", email="PAT@example.com"
        )
        contact.assigned_to.add(member)

        result = run(
            org_a,
            incoming(
                values={"email": "pat@example.com", "company_name": "Acme"},
                enquiry_text="Back again",
            ),
            django_capture_on_commit_callbacks,
        )

        assert result.result == "merged"
        assert result.lead.pk == lead.pk
        assert result.contact.pk == contact.pk
        assert Lead.objects.filter(org=org_a).count() == 1
        lead.refresh_from_db()
        assert lead.status == "converted"
        assert lead.company_name is None
        assert enquiries_on(contact).get().body == "Back again"
        assert comments_on(contact).count() == 0
        assert comments_on(lead).count() == 0
        assert sent == [
            (
                "enquired_again",
                (str(org_a.id),),
                {
                    "lead_id": None,
                    "contact_id": str(contact.id),
                    "channel_label": "webhook Ads",
                },
            )
        ]


class TestDuplicates:
    def test_the_same_external_id_is_a_duplicate_that_changes_nothing(
        self, org_a, sent, django_capture_on_commit_callbacks
    ):
        first = run(
            org_a, incoming(external_id="L-1"), django_capture_on_commit_callbacks
        )
        second = run(
            org_a,
            incoming(
                external_id="L-1",
                values={"email": "pat@example.com", "company_name": "Acme"},
                enquiry_text="again",
            ),
            django_capture_on_commit_callbacks,
        )
        assert second.result == "duplicate"
        assert second.lead.pk == first.lead.pk
        lead = Lead.objects.get(pk=first.lead.pk)
        assert lead.company_name is None
        # Only the first arrival's enquiry.
        assert enquiries_on(lead).count() == 1
        assert Lead.objects.filter(org=org_a).count() == 1
        assert sent == []

    def test_the_same_id_from_another_source_is_not_a_duplicate(
        self, org_a, django_capture_on_commit_callbacks
    ):
        run(org_a, incoming(external_id="L-1"), django_capture_on_commit_callbacks)
        other = run(
            org_a,
            incoming(
                external_id="L-1",
                external_source="intake:other",
                values={"email": "sam@example.com"},
            ),
            django_capture_on_commit_callbacks,
        )
        assert other.result == "created"

    def test_two_arrivals_racing_on_one_id_make_one_lead(
        self, org_a, django_capture_on_commit_callbacks
    ):
        """The second arrival looked before the first saved, so it found no
        match and its insert meets the unique constraint. It answers duplicate
        instead of failing."""
        first = run(
            org_a, incoming(external_id="L-1"), django_capture_on_commit_callbacks
        )
        real_match = intake._find_match
        misses = iter([True])

        def stale_then_real(org, data):
            if next(misses, False):
                return None, None
            return real_match(org, data)

        with mock.patch.object(intake, "_find_match", side_effect=stale_then_real):
            second = run(
                org_a,
                incoming(external_id="L-1", values={"email": "other@example.com"}),
                django_capture_on_commit_callbacks,
            )

        assert second.result == "duplicate"
        assert second.lead.pk == first.lead.pk
        assert Lead.objects.filter(org=org_a).count() == 1

    def test_a_race_on_an_email_merges_instead_of_failing(
        self, org_a, django_capture_on_commit_callbacks
    ):
        existing = Lead.objects.create(org=org_a, email="pat@example.com")
        real_match = intake._find_match
        misses = iter([True])

        def stale_then_real(org, data):
            if next(misses, False):
                return None, None
            return real_match(org, data)

        with mock.patch.object(intake, "_find_match", side_effect=stale_then_real):
            result = run(org_a, incoming(), django_capture_on_commit_callbacks)
        assert result.result == "merged"
        assert result.lead.pk == existing.pk

    def test_an_unrelated_integrity_error_is_not_swallowed(
        self, org_a, django_capture_on_commit_callbacks
    ):
        with (
            mock.patch.object(intake, "_create", side_effect=IntegrityError("boom")),
            pytest.raises(IntegrityError),
        ):
            run(org_a, incoming(), django_capture_on_commit_callbacks)


class TestLateArrivals:
    def _rule(self, org):
        return AutomationRule.objects.create(
            org=org, name="On lead", object_key="lead", is_active=True
        )

    def test_a_late_post_is_recorded_without_rules_or_email(
        self, org_a, member, sent, processed, django_capture_on_commit_callbacks
    ):
        self._rule(org_a)
        two_days_ago = timezone.now() - timedelta(days=2)
        result = run(
            org_a,
            incoming(assignee=member, occurred_at=two_days_ago),
            django_capture_on_commit_callbacks,
        )
        assert result.result == "created"
        assert processed == []
        assert sent == []
        lead = Lead.objects.get(pk=result.lead.pk)
        assert abs(lead.last_enquiry_at - two_days_ago) < timedelta(seconds=1)

    def test_a_recent_post_runs_rules_and_emails(
        self, org_a, member, sent, processed, django_capture_on_commit_callbacks
    ):
        self._rule(org_a)
        result = run(
            org_a,
            incoming(assignee=member, occurred_at=timezone.now() - timedelta(hours=23)),
            django_capture_on_commit_callbacks,
        )
        assert [c.record_id for c in processed] == [result.lead.pk]
        assert [name for name, _, _ in sent] == ["assigned"]

    def test_a_late_merge_does_not_move_the_last_enquiry_back(
        self, org_a, django_capture_on_commit_callbacks
    ):
        now = timezone.now()
        lead = Lead.objects.create(
            org=org_a, email="pat@example.com", last_enquiry_at=now
        )
        run(
            org_a,
            incoming(occurred_at=now - timedelta(days=3)),
            django_capture_on_commit_callbacks,
        )
        lead.refresh_from_db()
        assert lead.last_enquiry_at == now

    def test_a_future_timestamp_counts_as_now(
        self, org_a, django_capture_on_commit_callbacks
    ):
        result = run(
            org_a,
            incoming(occurred_at=timezone.now() + timedelta(days=30)),
            django_capture_on_commit_callbacks,
        )
        lead = Lead.objects.get(pk=result.lead.pk)
        assert lead.last_enquiry_at <= timezone.now()


class TestEnquiredAgainEmail:
    def _owner(self, org, email, active=True):
        user = User.objects.create_user(email=email, password="x")
        return Profile.objects.create(user=user, org=org, role="USER", is_active=active)

    def test_mails_the_active_owners_of_the_lead(self, org_a, mailoutbox):
        from leads.tasks import send_enquired_again_email

        lead = Lead.objects.create(org=org_a, first_name="Pat", last_name="Lee")
        lead.assigned_to.add(
            self._owner(org_a, "on@test.com"), self._owner(org_a, "off@test.com", False)
        )

        send_enquired_again_email(
            str(org_a.id), lead_id=str(lead.id), channel_label="webhook Ads"
        )

        [message] = mailoutbox
        assert message.recipients() == ["on@test.com"]
        assert message.subject == "Pat Lee enquired again"
        body = message.alternatives[0][0]
        assert f"/leads/{lead.id}" in body
        assert "webhook Ads" in body

    def test_a_contact_links_to_the_contact(self, org_a, mailoutbox):
        from leads.tasks import send_enquired_again_email

        contact = Contact.objects.create(org=org_a, first_name="Pat", last_name="Lee")
        contact.assigned_to.add(self._owner(org_a, "on@test.com"))

        send_enquired_again_email(str(org_a.id), contact_id=str(contact.id))

        assert f"/contacts/{contact.id}" in mailoutbox[0].alternatives[0][0]

    def test_another_orgs_record_sends_nothing(self, org_a, org_b, mailoutbox):
        from leads.tasks import send_enquired_again_email

        lead = Lead.objects.create(org=org_b, first_name="Pat")
        lead.assigned_to.add(self._owner(org_b, "b@test.com"))

        send_enquired_again_email(str(org_a.id), lead_id=str(lead.id))

        assert mailoutbox == []

    def test_a_name_with_a_line_break_still_sends(self, org_a, mailoutbox):
        from leads.tasks import send_enquired_again_email

        lead = Lead.objects.create(org=org_a, first_name="Pat\nBcc: x@evil.test")
        lead.assigned_to.add(self._owner(org_a, "on@test.com"))

        send_enquired_again_email(str(org_a.id), lead_id=str(lead.id))

        assert mailoutbox[0].subject == "Pat Bcc: x@evil.test enquired again"
        assert mailoutbox[0].recipients() == ["on@test.com"]


class TestWhatTheMergeKeeps:
    def test_a_different_email_and_number_go_into_the_enquiry(
        self, us_org, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=us_org, email="pat@example.com", phone="+1 555 123 4567"
        )
        run(
            us_org,
            incoming(
                values={"email": "PAT@example.com", "phone": "(555) 999-0000"},
                enquiry_text="Call me",
            ),
            django_capture_on_commit_callbacks,
        )
        lead.refresh_from_db()
        assert lead.phone == "+1 555 123 4567"
        body = enquiries_on(lead).get().body
        assert "Call me" in body
        assert "Phone: (555) 999-0000" in body
        # The same address in another case is not a conflict.
        assert "Email:" not in body

    def test_the_same_number_in_another_format_is_not_a_conflict(
        self, us_org, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=us_org, email="pat@example.com", phone="+1 555 123 4567"
        )
        run(
            us_org,
            incoming(values={"email": "pat@example.com", "phone": "555-123-4567"}),
            django_capture_on_commit_callbacks,
        )
        assert enquiries_on(lead).get().body == ""

    def test_a_phone_match_with_another_email_keeps_both(
        self, us_org, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=us_org, email="old@example.com", phone="+1 555 123 4567"
        )
        run(
            us_org,
            incoming(values={"email": "new@example.com", "phone": "555-123-4567"}),
            django_capture_on_commit_callbacks,
        )
        lead.refresh_from_db()
        assert lead.email == "old@example.com"
        assert "Email: new@example.com" in enquiries_on(lead).get().body

    def test_an_email_match_still_fills_a_blank_phone(
        self, us_org, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(org=us_org, email="pat@example.com")
        run(
            us_org,
            incoming(values={"email": "pat@example.com", "phone": "555-123-4567"}),
            django_capture_on_commit_callbacks,
        )
        lead.refresh_from_db()
        assert (lead.phone, lead.phone_e164) == ("555-123-4567", "+15551234567")
        assert enquiries_on(lead).get().body == ""


class TestReopenedStage:
    @pytest.fixture
    def pipeline(self, org_a):
        pipeline = LeadPipeline.objects.create(org=org_a, name="Inbound")
        stages = {}
        for order, (name, kind) in enumerate(
            [("Lost", "lost"), ("New", "open"), ("Working", "open"), ("Won", "won")]
        ):
            stages[name] = LeadStage.objects.create(
                org=org_a, pipeline=pipeline, name=name, order=order, stage_type=kind
            )
        return stages

    def test_a_closed_lead_moves_to_the_first_open_stage(
        self, org_a, pipeline, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a, email="pat@example.com", status="closed", stage=pipeline["Lost"]
        )
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        lead.refresh_from_db()
        assert (lead.status, lead.stage_id) == ("recycled", pipeline["New"].id)

    def test_a_closed_lead_on_an_open_stage_stays_there(
        self, org_a, pipeline, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a,
            email="pat@example.com",
            status="closed",
            stage=pipeline["Working"],
        )
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        lead.refresh_from_db()
        assert (lead.status, lead.stage_id) == ("recycled", pipeline["Working"].id)

    def test_an_open_lead_on_a_lost_stage_is_not_moved(
        self, org_a, pipeline, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a,
            email="pat@example.com",
            status="in process",
            stage=pipeline["Lost"],
        )
        run(org_a, incoming(), django_capture_on_commit_callbacks)
        lead.refresh_from_db()
        assert (lead.status, lead.stage_id) == ("in process", pipeline["Lost"].id)


class TestExternalIds:
    def test_a_long_id_is_cut_to_fit_and_still_matches(
        self, org_a, django_capture_on_commit_callbacks
    ):
        raw = "  <" + "m" * 296 + "@mail.test>  "
        first = run(
            org_a, incoming(external_id=raw), django_capture_on_commit_callbacks
        )
        lead = Lead.objects.get(pk=first.lead.pk)
        assert lead.external_id == raw.strip()[:255]
        again = run(
            org_a, incoming(external_id=raw), django_capture_on_commit_callbacks
        )
        assert (again.result, again.lead.pk) == ("duplicate", lead.pk)
        assert Lead.objects.filter(org=org_a).count() == 1

    def test_a_converted_lead_takes_the_id_so_a_retry_is_a_duplicate(
        self, org_a, sent, django_capture_on_commit_callbacks
    ):
        lead = Lead.objects.create(
            org=org_a, email="pat@example.com", status="converted"
        )
        Contact.objects.create(
            org=org_a, first_name="Pat", last_name="P", email="pat@example.com"
        )
        first = run(
            org_a,
            incoming(external_id="G-1", enquiry_text="Again"),
            django_capture_on_commit_callbacks,
        )
        lead.refresh_from_db()
        assert (first.result, lead.external_id) == ("merged", "G-1")
        again = run(
            org_a,
            incoming(external_id="G-1", enquiry_text="Again"),
            django_capture_on_commit_callbacks,
        )
        assert again.result == "duplicate"
        assert [name for name, _, _ in sent] == ["enquired_again"]
