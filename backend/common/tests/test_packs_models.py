import pytest

from common.models import Org, PackApplication
from common.rls import ORG_SCOPED_TABLES


@pytest.mark.django_db
def test_org_has_vertical_and_terminology_defaults():
    org = Org.objects.create(name="Acme")
    assert org.vertical == ""
    assert org.terminology == {}


@pytest.mark.django_db
def test_pack_application_records_result(org_a, admin_profile):
    app = PackApplication.objects.create(
        org=org_a,
        pack_id="real-estate",
        pack_version=1,
        applied_by=admin_profile,
        result={"created": [], "skipped": [], "failed": []},
    )
    assert app.org_id == org_a.id
    assert app.result["created"] == []


def test_pack_application_is_registered_for_rls():
    assert "pack_application" in ORG_SCOPED_TABLES
