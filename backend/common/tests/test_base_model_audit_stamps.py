"""`BaseModel.save()` stamps `created_by` / `updated_by`, and used to lose them.

The stamp comes from `crum.get_current_user`, a thread local that only the
request middleware fills. In a Celery worker, a management command, the shell or
a data migration it is None, and the old code answered that by assigning None to
both columns. Two consequences, both silent:

* an explicitly passed `created_by=` was discarded. `invoices.tasks.
  create_invoice_history` passes `created_by=invoice.created_by` and
  `updated_by=updated_by` from a task, so the invoice audit trail recorded
  nobody;
* on an UPDATE it assigned None to `created_by` too, so any save from a worker
  erased an existing row's creator for good.

Inside a request the request user still wins over anything in the payload, and
that is load-bearing rather than incidental: 15 serializers leave `created_by` or
`updated_by` writable, and this assignment is what keeps a forged value
harmless. `TestTheRequestUserStillWins` is the half that pins it.
"""

import pytest
from crum import impersonate

from common.models import Org, User
from leads.models import Lead


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="stamp-other@example.com", password="x", is_active=True
    )


@pytest.fixture
def stamp_org(db):
    return Org.objects.create(name="Stamp Org")


class TestOutsideARequestTheCallerDecides:
    """No request means no current user, and nothing to derive a stamp from."""

    def test_an_explicit_created_by_survives_create(self, db, stamp_org, other_user):
        lead = Lead.objects.create(
            title="explicit", org=stamp_org, created_by=other_user
        )

        lead.refresh_from_db()
        assert lead.created_by == other_user

    def test_an_explicit_updated_by_survives_create(self, db, stamp_org, other_user):
        lead = Lead.objects.create(
            title="explicit", org=stamp_org, updated_by=other_user
        )

        lead.refresh_from_db()
        assert lead.updated_by == other_user

    def test_a_later_save_does_not_erase_created_by(self, db, stamp_org, other_user):
        """The destructive half: an UPDATE from a worker nulled the creator."""
        lead = Lead.objects.create(
            title="explicit", org=stamp_org, created_by=other_user
        )

        lead.title = "renamed by a background task"
        lead.save()

        lead.refresh_from_db()
        assert lead.created_by == other_user

    def test_setting_the_attribute_then_saving_persists(
        self, db, stamp_org, other_user
    ):
        """Assignment then `save()`, the shape a data migration uses."""
        lead = Lead.objects.create(title="blank", org=stamp_org)

        lead.created_by = other_user
        lead.save()

        lead.refresh_from_db()
        assert lead.created_by == other_user

    def test_a_caller_that_says_nothing_still_gets_null(self, db, stamp_org):
        """The default is unchanged: no request and no explicit value is None."""
        lead = Lead.objects.create(title="silent", org=stamp_org)

        lead.refresh_from_db()
        assert lead.created_by is None
        assert lead.updated_by is None


class TestTheRequestUserStillWins:
    """Inside a request the server decides, whatever the payload said.

    `created_by` is writable on 15 serializers. This branch is what makes that
    harmless, so it must keep overwriting rather than deferring to the caller.
    """

    def test_created_by_is_overwritten_on_create(self, db, stamp_org, other_user):
        actor = User.objects.create_user(
            email="stamp-actor@example.com", password="x", is_active=True
        )

        with impersonate(actor):
            lead = Lead.objects.create(
                title="forged", org=stamp_org, created_by=other_user
            )

        lead.refresh_from_db()
        assert lead.created_by == actor

    def test_updated_by_is_overwritten_on_create(self, db, stamp_org, other_user):
        actor = User.objects.create_user(
            email="stamp-actor2@example.com", password="x", is_active=True
        )

        with impersonate(actor):
            lead = Lead.objects.create(
                title="forged", org=stamp_org, updated_by=other_user
            )

        lead.refresh_from_db()
        assert lead.updated_by == actor

    def test_created_by_is_not_touched_on_update(self, db, stamp_org, other_user):
        """Who made the row, not who last touched it."""
        creator = User.objects.create_user(
            email="stamp-creator@example.com", password="x", is_active=True
        )
        with impersonate(creator):
            lead = Lead.objects.create(title="mine", org=stamp_org)

        editor = User.objects.create_user(
            email="stamp-editor@example.com", password="x", is_active=True
        )
        with impersonate(editor):
            lead.title = "edited by someone else"
            lead.save()

        lead.refresh_from_db()
        assert lead.created_by == creator
        assert lead.updated_by == editor

    def test_an_anonymous_request_defers_to_the_caller(self, db, stamp_org, other_user):
        """`AnonymousUser` is treated as no user, the same as no request."""
        from django.contrib.auth.models import AnonymousUser

        with impersonate(AnonymousUser()):
            lead = Lead.objects.create(
                title="anon", org=stamp_org, created_by=other_user
            )

        lead.refresh_from_db()
        assert lead.created_by == other_user


class TestTheInvoiceAuditTrailRecordsSomebody:
    """The concrete caller that was losing both stamps.

    `create_invoice_history` runs in a worker and passes both columns
    explicitly, which is exactly the combination the old code discarded.

    Note the two types. `InvoiceHistory` overrides `updated_by` to point at
    `Profile` while the inherited `created_by` still points at `User`, so the
    task passes one of each. That override is also why this row must only ever
    be written from a worker: with a request user present, `BaseModel.save()`
    would assign a `User` to the `Profile` column and raise. Nothing sets
    `CELERY_TASK_ALWAYS_EAGER`, so today it cannot happen.
    """

    def test_history_keeps_the_two_users_the_task_passes(
        self, db, stamp_org, other_user
    ):
        from common.models import Profile
        from invoices.models import Invoice, InvoiceHistory

        editor = Profile.objects.create(
            user=User.objects.create_user(
                email="stamp-editor2@example.com", password="x", is_active=True
            ),
            org=stamp_org,
            role="USER",
            is_active=True,
        )
        invoice = Invoice.objects.create(
            invoice_title="INV-1", invoice_number="1", org=stamp_org
        )

        history = InvoiceHistory.objects.create(
            invoice=invoice,
            invoice_title=invoice.invoice_title,
            invoice_number=invoice.invoice_number,
            total_amount=10,
            currency="USD",
            amount_due=10,
            status="Draft",
            org=stamp_org,
            created_by=other_user,
            updated_by=editor,
        )

        history.refresh_from_db()
        assert history.created_by == other_user
        assert history.updated_by == editor
