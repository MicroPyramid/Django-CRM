import pytest

from common.models import CustomFieldDefinition, Tags
from common.packs.applier import apply_pack
from common.packs.loader import get_pack
from leads.models import LeadPipeline, LeadStage


@pytest.mark.django_db
def test_apply_creates_every_element_from_the_manifest(org_a, admin_profile):
    pack = get_pack("real-estate")
    report = apply_pack(org_a, pack, admin_profile)

    # Manifest↔database equivalence: counts per type must match the manifest.
    assert LeadPipeline.objects.filter(org=org_a).count() == 1
    assert LeadStage.objects.filter(org=org_a).count() == len(
        pack["lead_pipeline"]["stages"]
    )
    assert CustomFieldDefinition.objects.filter(org=org_a).count() == len(
        pack["custom_fields"]
    )
    # +1 for the reserved "Sample data" tag the applier creates alongside any
    # pack that carries a sample_data block (common/packs/applier.py).
    sample_tag_count = 1 if (pack.get("sample_data") or {}).get("leads") else 0
    assert (
        Tags.objects.filter(org=org_a).count() == len(pack["tags"]) + sample_tag_count
    )
    assert report["failed"] == []


@pytest.mark.django_db
def test_applied_stage_attributes_match_the_manifest(org_a, admin_profile):
    pack = get_pack("real-estate")
    apply_pack(org_a, pack, admin_profile)
    for spec in pack["lead_pipeline"]["stages"]:
        stage = LeadStage.objects.get(org=org_a, name=spec["name"])
        assert stage.order == spec["order"]
        assert stage.stage_type == spec["stage_type"]
        assert stage.color == spec["color"]


@pytest.mark.django_db
def test_second_apply_creates_nothing_and_mutates_nothing(org_a, admin_profile):
    pack = get_pack("real-estate")
    apply_pack(org_a, pack, admin_profile)
    org_a.refresh_from_db()

    before = {
        (t.__name__, str(row.id)): row.updated_at
        for t in (LeadPipeline, LeadStage, CustomFieldDefinition, Tags)
        for row in t.objects.filter(org=org_a)
    }
    # Org is the one row the applier IS allowed to write. The invariant only
    # holds if a no-op second apply leaves it untouched too.
    before_org = (org_a.vertical, dict(org_a.terminology))

    report = apply_pack(org_a, pack, admin_profile)

    after = {
        (t.__name__, str(row.id)): row.updated_at
        for t in (LeadPipeline, LeadStage, CustomFieldDefinition, Tags)
        for row in t.objects.filter(org=org_a)
    }
    org_a.refresh_from_db()
    after_org = (org_a.vertical, dict(org_a.terminology))

    assert report["created"] == []
    assert report["skipped"]
    # A report saying "skipped" does not prove nothing was written. This does.
    assert before == after
    assert before_org == after_org


@pytest.mark.django_db
def test_stale_org_reference_does_not_clobber_a_prior_apply(org_a, admin_profile):
    """No concurrency needed to reproduce this, just two Org references.

    `stale` is loaded before either apply_pack call, so it never observes
    real-estate's terminology/vertical write. If _apply_terminology decides
    from that stale in-memory snapshot instead of re-reading the row inside
    its own transaction, applying education-admissions through `stale`
    overwrites (not merges) real-estate's already-persisted terminology and
    clobbers org.vertical back to "" -> "education-admissions".
    """
    from common.models import Org

    stale = Org.objects.get(pk=org_a.pk)

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    apply_pack(stale, get_pack("education-admissions"), admin_profile)

    org_a.refresh_from_db()
    assert org_a.vertical == "real-estate"  # first pack's id, not clobbered
    # real-estate's keys must survive the second (stale-object) apply.
    assert org_a.terminology["opportunity.singular"] == "Deal"
    assert org_a.terminology["opportunity.plural"] == "Deals"
    # education-admissions' own keys were still added.
    assert org_a.terminology["contact.singular"] == "Student"


@pytest.mark.django_db
def test_existing_pipeline_of_same_name_skips_its_stages_too(org_a, admin_profile):
    LeadPipeline.objects.create(org=org_a, name="Sales")
    report = apply_pack(org_a, get_pack("real-estate"), admin_profile)

    assert LeadStage.objects.filter(org=org_a).count() == 0
    assert any(e["type"] == "lead_pipeline" for e in report["skipped"])


@pytest.mark.django_db
def test_applier_never_sets_a_default_pipeline(org_a, admin_profile):
    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    assert not LeadPipeline.objects.filter(org=org_a, is_default=True).exists()


@pytest.mark.django_db
def test_apply_writes_terminology_and_vertical(org_a, admin_profile):
    pack = get_pack("real-estate")
    apply_pack(org_a, pack, admin_profile)
    org_a.refresh_from_db()
    assert org_a.vertical == "real-estate"
    assert org_a.terminology["lead.plural"] == "Enquiries"


@pytest.mark.django_db
def test_terminology_is_not_overwritten_on_reapply(org_a, admin_profile):
    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    org_a.terminology["lead.plural"] = "Leads"
    org_a.save(update_fields=["terminology"])

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    org_a.refresh_from_db()
    assert org_a.terminology["lead.plural"] == "Leads"  # admin's edit wins


@pytest.mark.django_db
def test_apply_records_a_pack_application(org_a, admin_profile):
    from common.models import PackApplication

    apply_pack(org_a, get_pack("real-estate"), admin_profile)
    record = PackApplication.objects.get(org=org_a, pack_id="real-estate")
    assert record.applied_by_id == admin_profile.id
    assert record.result["created"]


@pytest.mark.django_db
def test_apply_pack_rejects_an_actor_from_a_different_org(org_a, org_b, admin_profile):
    """admin_profile belongs to org_a. Applying to org_b with that actor must
    be rejected outright, not silently create cross-org lead assignments;
    _apply_sample_data does lead.assigned_to.add(actor) with no org check of
    its own, so before this guard existed apply_pack(org_b, pack, admin_profile)
    assigned every sample lead it created in org_b to an org_a profile.
    """
    from leads.models import Lead

    with pytest.raises(ValueError):
        apply_pack(org_b, get_pack("real-estate"), admin_profile)

    assert not Lead.objects.filter(org=org_b).exists()


@pytest.mark.django_db
def test_apply_pack_allows_actor_from_the_same_org(org_a, admin_profile):
    # Sanity check for the guard above: it must not reject the ordinary case.
    report = apply_pack(org_a, get_pack("real-estate"), admin_profile)
    assert report["created"]
