"""A rule is paused when its owner stops being an admin of its org."""

from unittest import mock

import pytest
from django.utils import timezone

from automation import ownership
from automation.models import AutomationRule, AutomationRun
from common.models import Notification, Profile, User
from opportunity.models import DealPipeline, Opportunity

EMAIL = "automation.actions.send_member_email.delay"
NAME_CHANGES = {"event": "updated", "field": "name", "to": None}


def _member(org, name, *, role="ADMIN"):
    user = User.objects.create_user(
        email=f"{name.lower()}@example.com", password="x", name=name
    )
    return Profile.objects.create(user=user, org=org, role=role, is_active=True)


@pytest.fixture
def creator(org_a):
    return _member(org_a, "Creator")


def _rule(org, owner, name="Rule"):
    return AutomationRule.objects.create(
        org=org,
        name=name,
        object_key="deal",
        trigger=NAME_CHANGES,
        actions=[
            {
                "type": "set_field",
                "target": "record",
                "field": "amount",
                "value": 500,
            }
        ],
        owner=owner,
        is_active=True,
        switched_on_at=timezone.now(),
    )


def _paused(rule, code):
    rule.refresh_from_db()
    assert rule.is_active is False
    assert rule.paused_reason == code


def _told(profile):
    return Notification.objects.filter(recipient=profile, verb="automation.paused")


def test_demoting_the_owner_pauses_their_rules(admin_client, org_a, creator):
    rule = _rule(org_a, creator)
    response = admin_client.patch(
        f"/api/user/{creator.user.id}/", {"role": "USER"}, format="json"
    )
    assert response.status_code == 200
    _paused(rule, "not_admin")


def test_deactivating_the_owner_pauses_their_rules(admin_client, org_a, creator):
    rule = _rule(org_a, creator)
    response = admin_client.post(
        f"/api/user/{creator.user.id}/status/", {"status": "Inactive"}
    )
    assert response.status_code == 200
    _paused(rule, "deactivated")


def test_deactivating_the_owners_user_pauses_in_every_org(org_a, org_b, creator):
    other = Profile.objects.create(user=creator.user, org=org_b, role="ADMIN")
    first, second = _rule(org_a, creator), _rule(org_b, other)
    creator.user.is_active = False
    creator.user.save()
    _paused(first, "deactivated")
    _paused(second, "deactivated")


@mock.patch("common.views.user_views.send_email_user_delete")
def test_deleting_the_owners_profile_pauses_their_rules(
    _email, admin_client, org_a, creator
):
    rule = _rule(org_a, creator)
    assert admin_client.delete(f"/api/user/{creator.user.id}/").status_code == 200
    rule.refresh_from_db()
    assert rule.owner is None
    assert (rule.is_active, rule.paused_reason) == (False, "left")


def test_deleting_the_owners_user_pauses_their_rules(org_a, creator):
    rule = _rule(org_a, creator)
    creator.user.delete()
    rule.refresh_from_db()
    assert (rule.is_active, rule.paused_reason) == (False, "deleted_user")


def test_a_superuser_owner_who_loses_superuser_and_is_not_admin_pauses(org_a):
    user = User.objects.create_user(
        email="root@test.com", password="x", is_superuser=True
    )
    profile = Profile.objects.create(user=user, org=org_a, role="USER")
    rule = _rule(org_a, profile)
    user.is_superuser = False
    user.save(update_fields=["is_superuser"])
    _paused(rule, "not_admin")


def test_a_superuser_owner_who_is_still_admin_keeps_running(org_a):
    user = User.objects.create_user(
        email="root@test.com", password="x", is_superuser=True
    )
    profile = Profile.objects.create(user=user, org=org_a, role="USER")
    rule = _rule(org_a, profile)
    user.save()
    rule.refresh_from_db()
    assert rule.is_active is True


def test_other_admins_are_told(admin_client, org_a, admin_profile, creator):
    bystander = _member(org_a, "Bystander", role="USER")
    first, second = _rule(org_a, creator, "Alpha"), _rule(org_a, creator, "Beta")
    admin_client.patch(f"/api/user/{creator.user.id}/", {"role": "USER"}, format="json")
    [note] = _told(admin_profile)
    assert sorted(note.data["rules"]) == ["Alpha", "Beta"]
    assert note.data["reason"] == ownership.SENTENCES["not_admin"]
    assert note.link == "/settings/automation"
    assert not _told(creator).exists()
    assert not _told(bystander).exists()
    _paused(first, "not_admin")
    _paused(second, "not_admin")


def test_nobody_is_told_when_nothing_was_paused(
    admin_client, org_a, admin_profile, creator
):
    admin_client.patch(f"/api/user/{creator.user.id}/", {"role": "USER"}, format="json")
    assert not _told(admin_profile).exists()


def test_other_owners_rules_keep_running(admin_client, org_a, admin_profile, creator):
    mine = _rule(org_a, admin_profile, "Mine")
    theirs = _rule(org_a, creator, "Theirs")
    admin_client.patch(f"/api/user/{creator.user.id}/", {"role": "USER"}, format="json")
    mine.refresh_from_db()
    assert (mine.is_active, mine.paused_reason) == (True, "")
    _paused(theirs, "not_admin")


def test_another_orgs_rules_are_untouched(org_a, org_b, creator):
    elsewhere = Profile.objects.create(user=creator.user, org=org_b, role="ADMIN")
    kept = _rule(org_b, elsewhere)
    creator.role = "USER"
    creator.save()
    kept.refresh_from_db()
    assert kept.is_active is True


def test_pause_counts_a_rule_once(org_a, creator):
    rule = _rule(org_a, creator)
    assert ownership.pause([rule], ownership.NOT_ADMIN) == 1
    assert ownership.pause([rule], ownership.NOT_ADMIN) == 0


def test_deleting_the_org_does_not_trip_the_receiver(org_a, creator):
    _rule(org_a, creator)
    org_a.delete()
    assert not AutomationRule.objects.filter(owner_id=creator.pk).exists()


def test_a_rule_taken_over_meanwhile_is_not_paused(org_a, admin_profile, creator):
    rule = _rule(org_a, creator)
    stale = AutomationRule.objects.get(pk=rule.pk)
    AutomationRule.objects.filter(pk=rule.pk).update(owner=admin_profile)
    assert ownership.pause([stale], ownership.NOT_ADMIN) == 0
    rule.refresh_from_db()
    assert (rule.is_active, rule.paused_reason) == (True, "")
    assert not _told(admin_profile).exists()


def test_a_paused_rule_does_not_run(
    org_a, admin_profile, django_capture_on_commit_callbacks
):
    deal = Opportunity.objects.create(
        org=org_a,
        name="Acme",
        pipeline=DealPipeline.default_for(org_a),
        stage="QUALIFICATION",
    )
    rule = _rule(org_a, admin_profile)

    def rename(name):
        deal.name = name
        with django_capture_on_commit_callbacks(execute=True), mock.patch(EMAIL):
            deal.save()

    rename("Acme 2")
    assert AutomationRun.objects.filter(org=org_a, rule=rule).count() == 1
    deal.refresh_from_db()
    assert deal.amount == 500
    deal.amount = 1

    assert ownership.pause([rule], ownership.NOT_ADMIN) == 1
    rename("Acme 3")
    assert AutomationRun.objects.filter(org=org_a, rule=rule).count() == 1
    deal.refresh_from_db()
    assert deal.amount == 1
