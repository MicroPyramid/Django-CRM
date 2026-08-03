class EntityError(ValueError):
    pass


# Paths verified against backend/common/app_urls/__init__.py and each app's
# urls.py. Note: solutions are NOT served at a top-level /api/solutions/.
# They live under the cases app at /api/cases/solutions/ (see cases/urls.py).
ENTITIES = {
    "leads":         {"path": "/api/leads/",          "actions": ["convert", "add_comment"]},
    "contacts":      {"path": "/api/contacts/",       "actions": ["add_comment"]},
    "accounts":      {"path": "/api/accounts/",       "actions": ["add_comment"]},
    "opportunities": {"path": "/api/opportunities/",  "actions": ["add_comment"]},
    "tasks":         {"path": "/api/tasks/",          "actions": []},
    "cases":         {"path": "/api/cases/",          "actions": ["add_comment"]},
    "invoices":      {"path": "/api/invoices/",       "actions": ["send"]},
    "solutions":     {"path": "/api/cases/solutions/", "actions": []},
}

# Actions with an outward-facing / irreversible side effect (e.g. emailing a
# customer). Like crm_delete, these require an explicit confirm=True so an agent
# can't trigger them off a misread instruction. Keyed by action name across all
# entities. Keep it small and conservative.
CONFIRM_REQUIRED_ACTIONS = {"send"}


def resolve_path(entity, pk=None):
    if entity not in ENTITIES:
        raise EntityError(f"Unknown entity '{entity}'. Known: {', '.join(ENTITIES)}")
    base = ENTITIES[entity]["path"]
    return f"{base}{pk}/" if pk else base
