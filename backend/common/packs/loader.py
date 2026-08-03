"""Registry of vertical packs, built once from backend/packs/*.json.

Pack ids are dict keys, never filesystem paths. A caller-supplied id can only
hit or miss this dict, so there is no traversal or SSRF surface.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from common.packs.schema import PackValidationError, validate_manifest

logger = logging.getLogger(__name__)

PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"


@lru_cache(maxsize=1)
def get_registry() -> dict[str, dict]:
    registry: dict[str, dict] = {}
    if not PACKS_DIR.is_dir():
        return registry
    for path in sorted(PACKS_DIR.glob("*.json")):
        raw = json.loads(path.read_text())
        manifest = validate_manifest(raw)
        if manifest["id"] != path.stem:
            raise PackValidationError(
                f"{path.name}: manifest id {manifest['id']!r} must match the filename"
            )
        registry[manifest["id"]] = manifest
    return registry


def get_pack(pack_id: str) -> dict | None:
    """Look up a pack by id. Unknown ids, including anything path-shaped, return None."""
    return get_registry().get(pack_id)
