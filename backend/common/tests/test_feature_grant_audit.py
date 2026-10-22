from datetime import datetime, timezone

import pytest

from common.audit_log import SecurityAuditLog, audit_log


@pytest.mark.django_db
def test_grant_writes_one_row(org_a):
    expires = datetime(2027, 3, 1, 12, 0, tzinfo=timezone.utc)
    audit_log.feature_grant_changed(org_a, "example_feature", expires, note="test")

    row = SecurityAuditLog.objects.get(event_type="FEATURE_GRANT_CHANGED")
    assert row.org == org_a
    assert row.user is None
    assert row.description == "example_feature granted until 2027-03-01"
    assert row.metadata == {
        "feature": "example_feature",
        "expires_at": expires.isoformat(),
        "note": "test",
    }


@pytest.mark.django_db
def test_revoke_writes_one_row(org_a):
    audit_log.feature_grant_changed(org_a, "example_feature", None)

    row = SecurityAuditLog.objects.get(event_type="FEATURE_GRANT_CHANGED")
    assert row.org == org_a
    assert row.description == "example_feature grant revoked"
    assert row.metadata == {
        "feature": "example_feature",
        "expires_at": None,
        "note": "",
    }
