import pytest

from common.models import Tags
from common.packs.applier import apply_pack, clear_sample_data
from common.packs.loader import get_pack
from leads.models import Lead, LeadPipeline

SAMPLE_SLUG = "sample-data"


@pytest.mark.django_db
def test_apply_creates_sample_leads_tagged_as_sample(org_a, admin_profile):
    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    leads = Lead.objects.filter(org=org_a)
    assert leads.count() >= 8
    assert all(lead.tags.filter(slug=SAMPLE_SLUG).exists() for lead in leads)
    assert all(lead.is_sample for lead in leads)


@pytest.mark.django_db
def test_clear_removes_only_sample_rows(org_a, admin_profile):
    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    real = Lead.objects.create(org=org_a, title="A real enquiry", first_name="Real")

    result = clear_sample_data(org_a)

    assert result["deleted"]["sample_lead"] >= 8
    assert result["retained"] == {}
    assert Lead.objects.filter(org=org_a).count() == 1
    assert Lead.objects.filter(org=org_a).first().id == real.id
    # The reserved tag is a label only now; clear_sample_data must never
    # delete it (Critical fix: it also must never be the *deletion key*; see
    # test_clear_does_not_delete_a_real_lead_that_adopted_the_sample_tag
    # below). This assertion is intentionally the inverse of the original
    # brief's version, which had clear_sample_data delete the tag too.
    assert Tags.objects.filter(org=org_a, slug=SAMPLE_SLUG).exists()


@pytest.mark.django_db
def test_clear_does_not_touch_another_org(org_a, org_b, admin_profile, profile_b):
    # Each org is applied with an actor from that same org; apply_pack now
    # rejects a mismatched (org, actor) pair (see the org guard in
    # applier.py), so org_b's apply uses profile_b, not admin_profile.
    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    apply_pack(org_b, get_pack("real-estate"), profile_b)

    clear_sample_data(org_a)

    assert Lead.objects.filter(org=org_b).count() >= 8


@pytest.mark.django_db
def test_clear_does_not_delete_a_real_lead_that_adopted_the_sample_tag(
    org_a, admin_profile
):
    """Regression for the Critical finding: clear_sample_data must key off
    Lead.is_sample, never the "Sample data" tag. Tags.save() recomputes its
    slug on every save and the tag CRUD endpoints have no reserved-slug
    guard, so a real lead can end up carrying this tag several ways: a
    member attaching it from the ordinary tag picker (reproduced here), a
    tag getting renamed onto this slug, or a user's own pre-existing
    "Sample data" tag being adopted by an apply. None of those may destroy
    the lead.
    """
    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    sample_tag = Tags.objects.get(org=org_a, slug=SAMPLE_SLUG)

    real = Lead.objects.create(org=org_a, title="A real enquiry", first_name="Real")
    real.tags.add(sample_tag)  # the ordinary tag picker, not the applier

    result = clear_sample_data(org_a)

    # the genuine sample leads are still cleared
    assert result["deleted"]["sample_lead"] >= 8
    assert Lead.objects.filter(org=org_a, id=real.id).exists()
    real.refresh_from_db()
    assert real.is_sample is False


@pytest.mark.django_db
def test_a_colliding_email_skips_only_that_sample_lead(org_a, admin_profile):
    """Regression for Important 2: a pre-existing lead sharing a sample
    lead's email must not roll back the whole apply. Without a savepoint per
    lead, unique_lead_email_per_org's IntegrityError propagated out of
    apply_pack's outer @transaction.atomic and rolled back every
    pipeline/tag/custom-field write the same call had already made.
    """
    pack = get_pack("real-estate")
    colliding_email = pack["sample_data"]["leads"][0]["email"]
    Lead.objects.create(org=org_a, title="Already here", email=colliding_email)

    report = apply_pack(org_a, pack, admin_profile)

    assert LeadPipeline.objects.filter(org=org_a).exists()  # not rolled back
    created = [e for e in report["created"] if e["type"] == "sample_lead"]
    skipped = [e for e in report["skipped"] if e["type"] == "sample_lead"]
    assert len(created) == len(pack["sample_data"]["leads"]) - 1
    assert len(skipped) == 1


@pytest.mark.django_db
def test_apply_with_no_actor_still_creates_leads_unassigned(org_a):
    """Regression: actor is optional (mirrors PackApplication.applied_by
    being nullable). Before the fix, `lead.assigned_to.add(None)` on
    Postgres raised a NOT NULL violation on the through row that the
    per-lead except clause misdiagnosed as "duplicate email" and swallowed;
    apply_pack(org, pack, None) created zero leads and reported all of them
    skipped with a false reason. On SQLite (this whole suite) the same call
    was a silent no-op, so this test could not have caught the Postgres bug
    by itself: it only pins the now-intended behavior: creation must
    succeed, and no lead ends up with a None entry in assigned_to.
    """
    pack = get_pack("real-estate")
    report = apply_pack(org_a, pack, None)

    created = [e for e in report["created"] if e["type"] == "sample_lead"]
    assert len(created) == len(pack["sample_data"]["leads"])
    assert report["skipped"] == [] or all(
        e["type"] != "sample_lead" for e in report["skipped"]
    )

    leads = Lead.objects.filter(org=org_a, is_sample=True)
    assert leads.count() == len(pack["sample_data"]["leads"])
    for lead in leads:
        assert lead.assigned_to.count() == 0


@pytest.mark.django_db
def test_clear_sample_data_writes_an_audit_record(org_a, admin_profile):
    from common.audit_log import SecurityAuditLog

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    result = clear_sample_data(org_a, admin_profile)

    record = SecurityAuditLog.objects.filter(
        event_type="SAMPLE_DATA_CLEARED", org=org_a
    ).latest("created_at")
    assert record.user_id == admin_profile.user_id
    # The audit record carries the total across every sample model, which is
    # what the per-type breakdown sums to.
    assert record.metadata["deleted_count"] == sum(result["deleted"].values())


@pytest.mark.django_db
def test_sample_leads_are_assigned_to_the_applying_admin(org_a, admin_profile):
    """Important 3: without an assignee, the admin who applied the pack has
    no ordinary "my leads" query that reaches the rows they just created.
    """
    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    leads = Lead.objects.filter(org=org_a, is_sample=True)
    assert leads.count() >= 8
    assert all(admin_profile in lead.assigned_to.all() for lead in leads)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "pack_id", ["real-estate", "education-admissions", "professional-services"]
)
def test_sample_data_applies_cleanly_for_every_shipped_pack(
    org_a, admin_profile, pack_id
):
    """The only end-to-end coverage of education-admissions' and
    professional-services' sample_data blocks, everything else in this file
    exercises real-estate only. Both other packs carry opportunity_amount /
    currency (Minor 9) and a full set of remapped `source` values (Important
    4), so this is what actually proves those two packs' sample rows insert
    without a DecimalField/choices surprise, not just that the JSON is
    schema-valid.
    """
    pack = get_pack(pack_id)
    report = apply_pack(org_a, pack, admin_profile)

    assert report["failed"] == []
    leads = Lead.objects.filter(org=org_a, is_sample=True)
    assert leads.count() == len(pack["sample_data"]["leads"])
    for lead in leads:
        assert admin_profile in lead.assigned_to.all()
        assert lead.tags.filter(slug=SAMPLE_SLUG).exists()


# ---------------------------------------------------------------------------
# Sample data beyond leads: accounts, contacts, deals, tickets and tasks.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "pack_id", ["real-estate", "education-admissions", "professional-services"]
)
def test_apply_creates_every_sample_entity_type(org_a, admin_profile, pack_id):
    """Each pack's whole sample block inserts, not just its leads.

    Counting against the manifest rather than a literal catches the failure this
    is really guarding: a row silently skipped by _create_sample's except clause
    still leaves the apply "successful" with fewer records than the pack ships.
    """
    from accounts.models import Account
    from cases.models import Case
    from contacts.models import Contact
    from opportunity.models import Opportunity
    from tasks.models import Task

    pack = get_pack(pack_id)
    report = apply_pack(org_a, pack, admin_profile)
    assert report["failed"] == []

    sample = pack["sample_data"]
    for key, model in (
        ("accounts", Account),
        ("contacts", Contact),
        ("deals", Opportunity),
        ("tickets", Case),
        ("tasks", Task),
        ("leads", Lead),
    ):
        created = model.objects.filter(org=org_a, is_sample=True).count()
        assert created == len(sample[key]), (
            f"{pack_id}: expected {len(sample[key])} {key}, got {created}"
        )


@pytest.mark.django_db
def test_sample_references_resolve_to_sample_rows(org_a, admin_profile):
    """A referenced parent is wired up, and only ever to another sample row."""
    from accounts.models import Account
    from cases.models import Case
    from contacts.models import Contact
    from opportunity.models import Opportunity
    from tasks.models import Task

    apply_pack(org_a, get_pack("real-estate"), admin_profile)

    dana = Contact.objects.get(org=org_a, email="dana.whitfield@example.com")
    assert dana.account is not None
    assert dana.account.name == "Harbourline Developments"
    assert dana.account.is_sample
    # Both sides of the account/contact link. The FK alone leaves the account
    # page's contact list empty.
    assert dana in dana.account.contacts.all()

    deal = Opportunity.objects.get(org=org_a, name="Marina District 3 bed, Whitfield")
    assert deal.account == dana.account

    ticket = Case.objects.get(org=org_a, name="Parking allocation not confirmed")
    assert ticket.account == dana.account
    assert dana in ticket.contacts.all()
    assert ticket.stage is not None and ticket.stage.name == "With agent"

    task = Task.objects.get(org=org_a, title="Confirm second viewing time")
    assert task.opportunity == deal
    assert task.account_id is None and task.case_id is None and task.lead_id is None

    # Nothing sample-created points at a non-sample row.
    assert not Account.objects.filter(org=org_a, is_sample=False).exists()


@pytest.mark.django_db
def test_reapply_does_not_duplicate_sample_data(org_a, admin_profile):
    """The guard spans every sample model, so a second apply adds nothing."""
    from accounts.models import Account

    pack = get_pack("real-estate")
    apply_pack(org_a, pack, admin_profile)
    before = Account.objects.filter(org=org_a).count()

    report = apply_pack(org_a, pack, admin_profile)

    assert Account.objects.filter(org=org_a).count() == before
    assert any(s["type"] == "sample_data" for s in report["skipped"])


@pytest.mark.django_db
def test_clear_removes_every_sample_entity_type(org_a, admin_profile):
    from accounts.models import Account
    from cases.models import Case
    from contacts.models import Contact
    from opportunity.models import Opportunity
    from tasks.models import Task

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    result = clear_sample_data(org_a, admin_profile)

    assert result["retained"] == {}
    for model in (Account, Contact, Opportunity, Case, Task, Lead):
        assert not model.objects.filter(org=org_a).exists(), model


@pytest.mark.django_db
def test_clear_keeps_a_sample_account_carrying_a_real_deal(org_a, admin_profile):
    """The data-loss case. Opportunity.account is CASCADE, so deleting a sample
    account would take a real deal the user attached to it with no warning.
    """
    from accounts.models import Account
    from opportunity.models import Opportunity

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    account = Account.objects.get(org=org_a, name="Harbourline Developments")
    real_deal = Opportunity.objects.create(
        org=org_a, name="A real deal the user created", account=account
    )
    assert real_deal.is_sample is False

    result = clear_sample_data(org_a, admin_profile)

    assert result["retained"]["sample_account"] == 1
    assert Account.objects.filter(pk=account.pk).exists()
    assert Opportunity.objects.filter(pk=real_deal.pk).exists()
    # Every other sample account had nothing attached and is gone.
    assert Account.objects.filter(org=org_a, is_sample=True).count() == 1


@pytest.mark.django_db
def test_clear_keeps_a_sample_ticket_carrying_billable_time(org_a, admin_profile):
    """TimeEntry.case is CASCADE, billable hours logged against a demo ticket
    must survive a clear.
    """
    from django.utils import timezone

    from cases.models import Case, TimeEntry

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    ticket = Case.objects.get(org=org_a, name="Parking allocation not confirmed")
    entry = TimeEntry.objects.create(
        org=org_a, case=ticket, profile=admin_profile, started_at=timezone.now()
    )

    result = clear_sample_data(org_a, admin_profile)

    assert result["retained"]["sample_ticket"] == 1
    assert Case.objects.filter(pk=ticket.pk).exists()
    assert TimeEntry.objects.filter(pk=entry.pk).exists()
    # Retention has to propagate: Case.account is CASCADE, so keeping the ticket
    # is worthless if its sample account is deleted a step later and takes the
    # ticket, and the billable time, with it.
    assert result["retained"]["sample_account"] == 1
    ticket.refresh_from_db()
    assert ticket.account is not None


@pytest.mark.django_db
def test_clear_does_not_raise_when_a_sample_account_has_a_protected_invoice(
    org_a, admin_profile
):
    """Invoice.account is PROTECT: a naive delete raises ProtectedError and
    aborts the whole clear, leaving every sample record in place with no
    explanation. The retain rule has to cover PROTECT, not just CASCADE.
    """
    from accounts.models import Account
    from invoices.models import Invoice

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    account = Account.objects.get(org=org_a, name="Cedar Grove Estates")
    invoice = Invoice.objects.create(
        org=org_a,
        invoice_title="A real invoice",
        invoice_number="INV-REAL-1",
        account=account,
    )

    result = clear_sample_data(org_a, admin_profile)  # must not raise

    assert result["retained"]["sample_account"] == 1
    assert Account.objects.filter(pk=account.pk).exists()
    assert Invoice.objects.filter(pk=invoice.pk).exists()
    # The rest of the sample data still cleared. One blocked row must not
    # abort the whole operation.
    assert result["deleted"]["sample_lead"] == 25
