"""Records linked to a record, for rules to reach beyond its one parent.

The community ships no link hook. Another edition registers one from its
`AppConfig.ready`; a hook has `specs(org, object_key) -> list[LinkSpec]` and
`records(org, object_key, record, spec_id) -> list[Model]`.
"""

from dataclasses import dataclass

_HOOKS = []


@dataclass(frozen=True)
class LinkSpec:
    id: str
    label: str
    object_key: str


def register_link_hook(hook) -> None:
    if hook not in _HOOKS:
        _HOOKS.append(hook)


def link_specs(org, object_key) -> list[LinkSpec]:
    return [spec for hook in _HOOKS for spec in hook.specs(org, object_key)]


def linked_records(org, object_key, record, spec_id) -> list:
    """The records `spec_id` links to `record`, from the hook that offers it."""
    for hook in _HOOKS:
        if any(spec.id == spec_id for spec in hook.specs(org, object_key)):
            return list(hook.records(org, object_key, record, spec_id))
    return []
