from bcrm_mcp.entities import (
    CONFIRM_REQUIRED_ACTIONS,
    ENTITIES,
    EntityError,
    resolve_path,
)

MAX_LIMIT = 50


async def crm_search(client, entity, query=None, filters=None, limit=20, offset=0):
    """Search/list records of an entity. Returns compact rows."""
    params = dict(filters or {})
    if query:
        params["search"] = query
    params["limit"] = min(int(limit or 20), MAX_LIMIT)
    params["offset"] = max(int(offset or 0), 0)
    return await client.get(resolve_path(entity), params=params)


async def crm_get(client, entity, id):
    """Fetch a single record's full detail."""
    return await client.get(resolve_path(entity, id))


async def crm_create(client, entity, data):
    """Create a record. `data` is validated server-side by DRF."""
    return await client.post(resolve_path(entity), json=data)


async def crm_update(client, entity, id, data):
    """Partially update a record (PATCH)."""
    return await client.patch(resolve_path(entity, id), json=data)


async def crm_delete(client, entity, id, confirm=False):
    """Delete a record. Requires confirm=True (destructive)."""
    if not confirm:
        raise ValueError("Destructive op: pass confirm=true to delete.")
    return await client.delete(resolve_path(entity, id))


async def crm_action(client, entity, id, action, params=None, confirm=False):
    """Run a non-CRUD action (e.g. convert, add_comment). See list_actions().

    Outward-facing/irreversible actions (CONFIRM_REQUIRED_ACTIONS, e.g. `send`,
    which emails a customer) require confirm=True, mirroring crm_delete.
    """
    if entity not in ENTITIES:
        raise EntityError(f"Unknown entity '{entity}'.")
    allowed = ENTITIES[entity]["actions"]
    if action not in allowed:
        raise ValueError(f"Action '{action}' not allowed for {entity}. Allowed: {allowed}")
    if action in CONFIRM_REQUIRED_ACTIONS and not confirm:
        raise ValueError(
            f"Outward-facing op '{action}' has a real side effect "
            f"(e.g. emails a customer): pass confirm=true to proceed."
        )
    return await client.post(f"{resolve_path(entity, id)}{action}/", json=params or {})


def list_actions():
    """Return the allowed actions per entity."""
    return {e: cfg["actions"] for e, cfg in ENTITIES.items()}


async def crm_describe(client, entity):
    """Return writable/readable fields + enums for an entity (from the OpenAPI schema)."""
    if entity not in ENTITIES:
        raise EntityError(f"Unknown entity '{entity}'.")
    schema = await client.get("/schema/", params={"format": "json"})
    return _extract_entity_fields(schema, entity)


# --- OpenAPI schema extraction (defensive, dependency-free) -------------------

# Affixes that mark a write/request variant of a component schema. drf-spectacular
# names PATCH bodies 'Patched<Name>' (prefix) and others '<Name>Request'/'Create'
# (suffix). We use these to (a) recognise the canonical read shape vs write shapes,
# and (b) strip them when comparing a component name to an entity key.
_VARIANT_SUFFIXES = ("create", "request", "update", "list")
_VARIANT_PREFIXES = ("patched",)


def _singularize(word):
    """Crude singularizer good enough for our entity keys / component names.

    'leads'->'lead', 'opportunities'->'opportunity', 'cases'->'case',
    'boxes'->'box'. Only collapses 'es' to nothing when it follows a true
    sibilant cluster (ss/x/z/ch/sh); otherwise just drops a trailing 's'."""
    w = word.lower()
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith("es") and (
        w[:-2].endswith(("ss", "x", "z", "ch", "sh"))
    ):
        return w[:-2]
    if w.endswith("s"):
        return w[:-1]
    return w


def _strip_variant(base):
    """Strip a leading/trailing variant affix from a lowercased name."""
    for prefix in _VARIANT_PREFIXES:
        if base.startswith(prefix) and len(base) > len(prefix):
            return base[len(prefix):]
    for suffix in _VARIANT_SUFFIXES:
        if base.endswith(suffix) and len(base) > len(suffix):
            return base[: -len(suffix)]
    return base


def _normalize_component_name(name):
    """Lowercase a component name, strip a variant affix, then singularize.
    e.g. 'LeadCreate'->'lead', 'Contacts'->'contact', 'PatchedLead'->'lead'."""
    return _singularize(_strip_variant(name.lower()))


def _component_variant(name):
    """Return the variant affix found in a component name, or '' for the read
    shape. Used to prefer the affix-less component as the canonical shape."""
    low = name.lower()
    if _strip_variant(low) != low:
        for affix in _VARIANT_PREFIXES + _VARIANT_SUFFIXES:
            if low.startswith(affix) or low.endswith(affix):
                return affix
    return ""


def _extract_entity_fields(schema, entity):
    """Walk an OpenAPI 3 dict and return a field map for `entity`.

    Result shape: {field_name: {"type": str, "required": bool, "enum": [...]?}}
    Returns {} (never raises) when no component matches: graceful degradation.
    """
    if not isinstance(schema, dict):
        return {}
    components = (schema.get("components") or {}).get("schemas") or {}
    if not isinstance(components, dict):
        return {}

    target = _singularize(entity)

    # Collect components whose normalized name matches the entity.
    matches = [
        name
        for name in components
        if _normalize_component_name(name) == target
    ]
    if not matches:
        return {}

    # Prefer the read shape (no variant suffix) for the field/type info; fall
    # back to whatever matched. Sort so suffix-less names come first.
    matches.sort(key=lambda n: (_component_variant(n) != "", n))
    read_name = matches[0]
    read_comp = components.get(read_name) or {}

    result = {}
    props = read_comp.get("properties") or {}
    required = set(read_comp.get("required") or [])

    for field, spec in props.items():
        if not isinstance(spec, dict):
            result[field] = {"type": "object", "required": field in required}
            continue
        entry = {
            "type": _resolve_type(spec, components),
            "required": field in required,
        }
        enum = _resolve_enum(spec, components)
        if enum is not None:
            entry["enum"] = enum
        result[field] = entry

    # Merge `required` from any write/request variant, DRF often marks fields
    # required only on the create/request serializer.
    for name in matches:
        if name == read_name:
            continue
        comp = components.get(name) or {}
        for field in comp.get("required") or []:
            if field in result:
                result[field]["required"] = True

    return result


def _ref_name(ref):
    """'#/components/schemas/Foo' -> 'Foo'."""
    if isinstance(ref, str) and "/" in ref:
        return ref.rsplit("/", 1)[-1]
    return ref


def _resolve_type(spec, components):
    """Shallow type resolution: scalar type, ref name, or 'object'."""
    if "type" in spec:
        return spec["type"]
    if "$ref" in spec:
        return _ref_name(spec["$ref"]) or "object"
    if "allOf" in spec and isinstance(spec["allOf"], list):
        for sub in spec["allOf"]:
            if isinstance(sub, dict) and "$ref" in sub:
                return _ref_name(sub["$ref"]) or "object"
        return "object"
    return "object"


def _resolve_enum(spec, components):
    """Return an enum list if present on the property or its (shallow) ref."""
    if isinstance(spec.get("enum"), list):
        return spec["enum"]
    # enum sometimes lives on a referenced component (allOf -> $ref -> enum).
    refs = []
    if "$ref" in spec:
        refs.append(spec["$ref"])
    for sub in spec.get("allOf") or []:
        if isinstance(sub, dict) and "$ref" in sub:
            refs.append(sub["$ref"])
    for ref in refs:
        comp = components.get(_ref_name(ref))
        if isinstance(comp, dict) and isinstance(comp.get("enum"), list):
            return comp["enum"]
    return None
