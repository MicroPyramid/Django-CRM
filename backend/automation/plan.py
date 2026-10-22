"""Whether an org's plan lets a rule switch on or run.

The community counts nothing: every rule may switch on and every active rule
runs. Another edition registers one hook from its `AppConfig.ready`, with
`may_switch_on(org, rule) -> str | None` and `runnable(org, rules) -> Runnable`.
"""

from dataclasses import dataclass

# At most one hook: two plans answering for one org would disagree.
_HOOKS = []


@dataclass(frozen=True)
class Runnable:
    rule_ids: frozenset
    statuses: dict
    summary: str | None


def register_plan_hook(hook) -> None:
    if _HOOKS and _HOOKS[0] is not hook:
        raise RuntimeError("A plan hook is already registered.")
    _HOOKS[:] = [hook]


def may_switch_on(org, rule) -> str | None:
    """`None` when the rule may switch on, else the refusal to show."""
    if not _HOOKS:
        return None
    return _HOOKS[0].may_switch_on(org, rule)


def runnable(org, rules) -> Runnable:
    """Which of the org's active `rules` run, with any status text for the rest."""
    if not _HOOKS:
        return Runnable(frozenset(rule.id for rule in rules), {}, None)
    return _HOOKS[0].runnable(org, rules)
