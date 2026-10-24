"""Record each org that applied a pack before apps existed as having installed it.

One `installed_app` row per org and pack, from the org's `pack_application`
runs of that pack: the latest run's version, actor and time. `offered` is every
part the runs' reports name, created or skipped, with a part skipped because
its module was off marked with that module; a later run's outcome wins.
`owned` is what a run created, found by natural key among rows that existed when
the latest run creating it was recorded (the applier writes a run's parts before
its `pack_application` row), so a part the org has since deleted is offered but
not owned, and a row the org made again under the same key is not the app's. Reports written before this
release name parts rather than keys; `_parts` maps them against the live
catalogue (`common.packs.loader`). A pack no longer in the catalogue gets no
row, and a pack the org already has a row for keeps it.

THE ORG LOOP IS NOT DECORATION. Every table read here except `organization`
is under FORCE ROW LEVEL SECURITY keyed on `app.current_org`, which is empty
during a migration (common/0042 explains). Orgs are walked by primary key in
batches, each in its own transaction with its context set.

REVERSE deletes the rows still exactly as this wrote them: installed, at the
version, time and actor of the org's latest run of that pack. A row an
install, update or removal has written since records a real action and stays.
"""

from django.db import migrations, transaction

# The live rules, as common/0042 does: one function owns the tag slug, and the
# catalogue is what a report's names are read against.
from common.models import Tags as LiveTags
from common.packs.loader import get_registry

BATCH = 500
MODULE_OFF = "is switched off for this organization."

# Frozen here so a later change to the live maps cannot change what this did.
PIPELINE_KINDS = {
    "lead_pipeline": ("lead", "leads", ("leads", "LeadPipeline", "LeadStage")),
    "case_pipeline": ("ticket", "tickets", ("cases", "CasePipeline", "CaseStage")),
    "task_pipeline": ("task", "tasks", ("tasks", "TaskPipeline", "TaskStage")),
}
FIELD_TARGETS = {
    "Lead": ("lead", "leads"),
    "Contact": ("contact", None),
    "Account": ("account", None),
    "Opportunity": ("deal", "deals"),
    "Case": ("ticket", "tickets"),
    "Task": ("task", "tasks"),
    "Invoice": ("invoice", "invoices"),
    "Estimate": ("estimate", "invoices"),
    "RecurringInvoice": ("recurring_invoice", "invoices"),
}
WORDING_TARGETS = {
    "lead": "lead",
    "opportunity": "deal",
    "contact": "contact",
    "account": "account",
    "invoice": "invoice",
}
# Product names the manifests carried before 2026-08-03, by SKU. They held
# the character below where the names now hold a comma.
_OLD = chr(0x2014)
RENAMED_PRODUCTS = {
    f"Monthly retainer {_OLD} Growth": "PS-RET-GROWTH",
    f"IELTS Coaching {_OLD} 8 week": "ED-IELTS-8W",
    f"SAT Prep {_OLD} 12 week": "ED-SAT-12W",
    f"Spoken English {_OLD} evening batch": "ED-SPEAK-EVE",
}


def _parts(result, pack):
    """``(ref, skipped_module, created)`` for each part a run's report names."""
    if not isinstance(result, dict):
        return []
    if isinstance(result.get("offered"), list):
        return [
            ((e["type"], e["target"], e["key"]), e["skipped_module"], e["created"])
            for e in result["offered"]
        ]
    skus = {p["name"]: p["sku"] for p in pack.get("products") or []}
    skus.update(
        (name, sku) for name, sku in RENAMED_PRODUCTS.items() if sku in skus.values()
    )
    sources = {s["label"]: s["key"] for s in pack.get("lead_sources") or []}
    fields = {f["key"]: f["target"] for f in pack.get("custom_fields") or []}
    created = [e for e in result.get("created") or [] if isinstance(e, dict)]
    skipped = [e for e in result.get("skipped") or [] if isinstance(e, dict)]
    made = {e.get("type"): e.get("name") for e in created}
    out = []
    for entry, was_created in [(e, True) for e in created] + [
        (e, False) for e in skipped
    ]:
        kind, name = entry.get("type"), entry.get("name")
        off = str(entry.get("reason", "")).endswith(MODULE_OFF)
        if not isinstance(kind, str) or not isinstance(name, str):
            continue
        if kind in PIPELINE_KINDS:
            target, module, _models = PIPELINE_KINDS[kind]
            module = module if off else None
            out.append((("pipeline", target, name), module, was_created))
            spec = pack.get(kind) or {}
            if not was_created and spec.get("name") == name:
                # A skipped pipeline's stages were skipped with it, unreported.
                for stage in spec.get("stages") or []:
                    key = f"{name}/{stage['name']}"
                    out.append((("stage", target, key), module, False))
        elif kind.endswith("_stage") and kind[: -len("_stage")] in PIPELINE_KINDS:
            pipeline_kind = kind[: -len("_stage")]
            pipeline = made.get(pipeline_kind) or (pack.get(pipeline_kind) or {}).get(
                "name"
            )
            target = PIPELINE_KINDS[pipeline_kind][0]
            out.append((("stage", target, f"{pipeline}/{name}"), None, was_created))
        elif kind == "custom_field":
            target_model = fields.get(name, "Lead")
            target, module = FIELD_TARGETS.get(
                target_model, (target_model.lower(), None)
            )
            out.append((("field", target, name), module if off else None, was_created))
        elif kind == "tag":
            out.append((("tag", None, LiveTags.slug_for(name)), None, was_created))
        elif kind == "lead_source":
            key = sources.get(name) or " ".join(name.lower().split())
            out.append((("source", None, key), None, was_created))
        elif kind == "product" and name in skus:
            module = "invoices" if off else None
            out.append((("product", None, skus[name]), module, was_created))
        elif kind == "terminology":
            target = WORDING_TARGETS.get(name.partition(".")[0])
            out.append((("wording", target, name), None, was_created))
    return out


def _owned(apps, org_id, created):
    """``created`` (ref to the time of the latest run that created it) as
    ``owned`` entries, for the rows the org still holds from those runs."""
    Org = apps.get_model("common", "Org")
    terms = Org.objects.get(pk=org_id).terminology
    terms = terms if isinstance(terms, dict) else {}
    models = {
        "field": apps.get_model("common", "CustomFieldDefinition"),
        "tag": apps.get_model("common", "Tags"),
        "source": apps.get_model("leads", "LeadSource"),
        "product": apps.get_model("invoices", "Product"),
    }
    lookups = {"tag": "slug", "source": "key", "product": "sku"}
    field_models = {target: model for model, (target, _m) in FIELD_TARGETS.items()}
    pipelines = {}
    for _kind, (target, _module, (app, pipeline, stage)) in PIPELINE_KINDS.items():
        pipelines[target] = (apps.get_model(app, pipeline), apps.get_model(app, stage))

    owned, found_pipelines = [], {}
    # Pipelines first, so a stage is looked up under the one this app owns.
    refs = sorted(created.items(), key=lambda item: item[0][0] == "stage")
    for (type_, target, key), when in refs:
        row = None
        if type_ == "wording":
            if key in terms:
                owned.append({"type": type_, "target": target, "key": key, "id": None})
            continue
        if type_ == "pipeline" and target in pipelines:
            row = (
                pipelines[target][0]
                .objects.filter(org_id=org_id, name=key, created_at__lte=when)
                .order_by("-created_at")
                .first()
            )
            if row is not None:
                found_pipelines[target] = row
        elif type_ == "stage" and target in found_pipelines:
            pipeline = found_pipelines[target]
            prefix = f"{pipeline.name}/"
            if key.startswith(prefix):
                row = (
                    pipelines[target][1]
                    .objects.filter(
                        pipeline=pipeline,
                        name=key[len(prefix) :],
                        created_at__lte=when,
                    )
                    .order_by("-created_at")
                    .first()
                )
        elif type_ == "field" and target in field_models:
            row = (
                models["field"]
                .objects.filter(
                    org_id=org_id,
                    target_model=field_models[target],
                    key=key,
                    created_at__lte=when,
                )
                .first()
            )
        elif type_ in lookups:
            row = (
                models[type_]
                .objects.filter(
                    org_id=org_id, created_at__lte=when, **{lookups[type_]: key}
                )
                .first()
            )
        if row is not None:
            owned.append(
                {"type": type_, "target": target, "key": key, "id": str(row.pk)}
            )
    return owned


def backfill_org(apps, org_id, registry):
    PackApplication = apps.get_model("common", "PackApplication")
    InstalledApp = apps.get_model("common", "InstalledApp")
    runs = {}
    for run in PackApplication.objects.filter(org_id=org_id).order_by("created_at"):
        runs.setdefault(run.pack_id, []).append(run)
    if not runs:
        return
    have = set(
        InstalledApp.objects.filter(org_id=org_id).values_list("app_id", flat=True)
    )
    for pack_id, pack_runs in runs.items():
        pack = registry.get(pack_id)
        if pack is None or pack_id in have:
            continue
        offered, created = {}, {}
        for run in pack_runs:
            for ref, module, was_created in _parts(run.result, pack):
                offered[ref] = module
                if was_created:
                    created[ref] = run.created_at
        latest = pack_runs[-1]
        InstalledApp.objects.create(
            org_id=org_id,
            app_id=pack_id,
            installed_version=latest.pack_version,
            status="installed",
            installed_by_id=latest.applied_by_id,
            installed_at=latest.created_at,
            owned=_owned(apps, org_id, created),
            offered=[
                {"type": t, "target": target, "key": k, "skipped_module": module}
                for (t, target, k), module in offered.items()
            ],
        )


def _each_org(apps, schema_editor, per_org):
    connection = schema_editor.connection
    Org = apps.get_model("common", "Org")

    def set_context(value):
        if connection.vendor != "postgresql":
            return
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('app.current_org', %s, false)", [value])

    last = None
    try:
        while True:
            batch = Org.objects.order_by("pk")
            if last is not None:
                batch = batch.filter(pk__gt=last)
            ids = list(batch.values_list("pk", flat=True)[:BATCH])
            if not ids:
                break
            for org_id in ids:
                set_context(str(org_id))
                with transaction.atomic(using=connection.alias):
                    per_org(org_id)
            last = ids[-1]
    finally:
        set_context("")


def backfill_installed_apps(apps, schema_editor):
    registry = get_registry()
    _each_org(apps, schema_editor, lambda org_id: backfill_org(apps, org_id, registry))


def remove_backfilled_apps(apps, schema_editor):
    PackApplication = apps.get_model("common", "PackApplication")
    InstalledApp = apps.get_model("common", "InstalledApp")

    def per_org(org_id):
        latest = {}
        for run in PackApplication.objects.filter(org_id=org_id).order_by("created_at"):
            latest[run.pack_id] = run
        for row in InstalledApp.objects.filter(org_id=org_id, status="installed"):
            run = latest.get(row.app_id)
            if run is not None and (
                row.installed_version,
                row.installed_at,
                row.installed_by_id,
            ) == (run.pack_version, run.created_at, run.applied_by_id):
                row.delete()

    _each_org(apps, schema_editor, per_org)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("common", "0061_enable_rls_installed_app"),
        ("leads", "0022_lead_response_fields"),
        ("cases", "0034_inboundmailbox_lead_fields"),
        ("tasks", "0014_unassign_non_members_from_board_cards"),
        ("invoices", "0014_add_zar_currency"),
    ]

    operations = [
        migrations.RunPython(backfill_installed_apps, remove_backfilled_apps),
    ]
