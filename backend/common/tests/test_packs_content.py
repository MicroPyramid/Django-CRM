import pytest

from common.packs.loader import get_registry
from common.packs.schema import SAMPLE_ENTITY_KEYS

SHIPPED = {
    "real-estate",
    "education-admissions",
    "professional-services",
    "events-weddings",
}


def test_all_shipped_packs_load_and_validate():
    # get_registry() validates every file; this is the CI gate that a malformed
    # pack fails here rather than at a user's signup.
    assert SHIPPED <= set(get_registry())


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_pack_has_terminology_and_a_lead_pipeline(pack_id):
    pack = get_registry()[pack_id]
    assert pack["terminology"], f"{pack_id} must rename at least one label"
    assert pack["lead_pipeline"]["stages"], f"{pack_id} needs lead stages"


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_lead_pipeline_has_exactly_one_won_and_one_lost_stage(pack_id):
    stages = get_registry()[pack_id]["lead_pipeline"]["stages"]
    types = [s.get("stage_type", "open") for s in stages]
    assert types.count("won") == 1
    assert types.count("lost") == 1


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_sample_data_has_a_plausible_number_of_leads(pack_id):
    # Enough to fill a list page and make the kanban look worked-in, without
    # making the demo org feel like a data dump the user has to clear out.
    leads = get_registry()[pack_id]["sample_data"]["leads"]
    assert 20 <= len(leads) <= 40, f"{pack_id} has {len(leads)} sample leads"


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_pack_ships_all_three_pipelines(pack_id):
    """A pack that configures only leads leaves the tickets and tasks boards
    empty of columns, which reads as a broken feature rather than an unused one.
    """
    pack = get_registry()[pack_id]
    for key in ("lead_pipeline", "case_pipeline", "task_pipeline"):
        assert pack.get(key, {}).get("stages"), f"{pack_id} is missing {key}"


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_products_have_unique_skus(pack_id):
    # (org, sku) is the applier's match key. Two products sharing a sku inside
    # one pack would make the second a permanent skip.
    skus = [p["sku"] for p in get_registry()[pack_id].get("products") or []]
    assert skus, f"{pack_id} ships no products"
    assert len(skus) == len(set(skus)), f"{pack_id} has duplicate skus"


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_sample_data_covers_every_entity_type(pack_id):
    """Every module the nav offers should have something in it after an apply.

    A pack with leads but no accounts leaves most of the CRM empty, which is the
    gap this content set exists to close.
    """
    sample = get_registry()[pack_id]["sample_data"]
    for key in SAMPLE_ENTITY_KEYS:
        assert sample.get(key), f"{pack_id} has no sample {key}"


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_every_sample_task_hangs_off_something(pack_id):
    """An unparented task is legal but reads as orphaned in the UI."""
    pack = get_registry()[pack_id]
    for task in pack["sample_data"]["tasks"]:
        parents = [p for p in ("account", "deal", "ticket", "lead") if task.get(p)]
        assert len(parents) == 1, (
            f"{pack_id}: sample task {task['title']!r} has parents {parents}, expected exactly one"
        )


@pytest.mark.parametrize("pack_id", sorted(SHIPPED))
def test_every_sample_lead_stage_matches_the_packs_own_pipeline(pack_id):
    pack = get_registry()[pack_id]
    stage_names = {s["name"] for s in pack["lead_pipeline"]["stages"]}
    for lead in pack["sample_data"]["leads"]:
        assert lead.get("stage") in stage_names, (
            f"{pack_id}: sample lead {lead['title']!r} has stage "
            f"{lead.get('stage')!r}, not one of {sorted(stage_names)}"
        )
