import pytest

from common.packs.loader import get_pack, get_registry
from common.packs.schema import PackValidationError, validate_manifest


def _minimal():
    return {"id": "demo", "version": 1, "name": "Demo"}


def test_minimal_manifest_validates():
    assert validate_manifest(_minimal())["id"] == "demo"


def test_unknown_top_level_key_is_rejected():
    raw = _minimal() | {"wat": 1}
    with pytest.raises(PackValidationError, match="wat"):
        validate_manifest(raw)


def test_is_default_is_rejected_anywhere():
    raw = _minimal() | {
        "lead_pipeline": {"name": "Sales", "is_default": True, "stages": []}
    }
    with pytest.raises(PackValidationError, match="is_default"):
        validate_manifest(raw)


def test_product_without_sku_is_rejected():
    raw = _minimal() | {"products": [{"name": "Course", "price": "100.00"}]}
    with pytest.raises(PackValidationError, match="sku"):
        validate_manifest(raw)


def test_unknown_custom_field_target_is_rejected():
    raw = _minimal() | {
        "custom_fields": [
            {"target": "Property", "key": "x", "label": "X", "field_type": "text"}
        ]
    }
    with pytest.raises(PackValidationError, match="Property"):
        validate_manifest(raw)


def test_win_probability_rejected_on_non_lead_stage():
    raw = _minimal() | {
        "case_pipeline": {
            "name": "Support",
            "stages": [{"name": "New", "win_probability": 50}],
        }
    }
    with pytest.raises(PackValidationError, match="win_probability"):
        validate_manifest(raw)


def test_unknown_tag_color_is_rejected():
    raw = _minimal() | {"tags": [{"name": "Hot", "color": "chartreuse"}]}
    with pytest.raises(PackValidationError, match="chartreuse"):
        validate_manifest(raw)


def test_lead_stage_accepts_won():
    raw = _minimal() | {
        "lead_pipeline": {
            "name": "Sales",
            "stages": [{"name": "Closed Won", "stage_type": "won"}],
        }
    }
    stages = validate_manifest(raw)["lead_pipeline"]["stages"]
    assert stages[0]["stage_type"] == "won"


def test_case_stage_accepts_closed():
    raw = _minimal() | {
        "case_pipeline": {
            "name": "Support",
            "stages": [{"name": "Resolved", "stage_type": "closed"}],
        }
    }
    stages = validate_manifest(raw)["case_pipeline"]["stages"]
    assert stages[0]["stage_type"] == "closed"


def test_case_stage_rejects_won():
    raw = _minimal() | {
        "case_pipeline": {
            "name": "Support",
            "stages": [{"name": "Resolved", "stage_type": "won"}],
        }
    }
    with pytest.raises(PackValidationError, match="stage_type"):
        validate_manifest(raw)


def test_task_stage_accepts_in_progress():
    raw = _minimal() | {
        "task_pipeline": {
            "name": "Delivery",
            "stages": [{"name": "Doing", "stage_type": "in_progress"}],
        }
    }
    stages = validate_manifest(raw)["task_pipeline"]["stages"]
    assert stages[0]["stage_type"] == "in_progress"


def test_registry_lookup_of_unknown_id_returns_none():
    assert get_pack("no-such-pack") is None


def test_registry_cannot_be_traversed():
    assert get_pack("../../etc/passwd") is None
    assert get_pack("real-estate/../demo") is None
