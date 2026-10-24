from dataclasses import replace

from django.core.exceptions import ValidationError

from automation.adapters import same_org
from automation.adapters.leads import source_choices
from automation.objects import Adapter, Choice, FieldSpec, model_choices
from opportunity.models import DealStage, Opportunity
from opportunity.updates import update_deal
from opportunity.workflow import STAGE_KINDS
from webhooks.events import deal_data

NOT_A_STAGE = "That is not a stage of this deal's pipeline."


class DealAdapter(Adapter):
    parent_key = "account"
    route = "/pipeline/{id}"
    FIELDS = (
        FieldSpec("name", "Deal name", "text"),
        # By stage id: every pipeline is seeded with the same codes.
        FieldSpec("stage", "Stage", "choice"),
        # "Won in any pipeline" as one field, matched by kind like `deal.won`.
        FieldSpec(
            "stage_kind",
            "Outcome",
            "choice",
            tuple(
                Choice(value, f"{label} (any pipeline)") for value, label in STAGE_KINDS
            ),
            settable=False,
        ),
        FieldSpec(
            "opportunity_type",
            "Type",
            "choice",
            model_choices(Opportunity, "opportunity_type"),
        ),
        FieldSpec("lead_source", "Source", "choice"),
        FieldSpec("amount", "Amount", "number"),
        FieldSpec("probability", "Probability", "number"),
        FieldSpec("closed_on", "Close date", "date"),
        FieldSpec("assigned_to", "Assigned to", "people"),
    )

    def own_fields(self, org):
        stages = tuple(
            Choice(str(stage.pk), stage.label, stage.pipeline.name)
            for stage in DealStage.objects.filter(org=org, pipeline__org=org)
            .select_related("pipeline")
            .order_by("-pipeline__is_default", "pipeline__name", "order", "created_at")
        )
        choices = {"stage": stages, "lead_source": source_choices(org)}
        return [
            replace(s, choices=choices[s.key]) if s.key in choices else s
            for s in self.FIELDS
        ]

    def read(self, record, key):
        if key in ("stage", "stage_kind"):
            stage = record.current_stage()
            if stage is None:
                return None
            return str(stage.pk) if key == "stage" else stage.kind
        return super().read(record, key)

    def name(self, record):
        return record.name

    def parent(self, record):
        account = same_org(record, "account")
        return ("account", account) if account is not None else None

    def task_parent(self, record):
        return {"opportunity": str(record.pk)}

    def webhook_data(self, record):
        return deal_data(record)

    def update(self, request, record, data):
        if "stage" in data:
            try:
                stage = DealStage.objects.filter(
                    pk=data["stage"],
                    org_id=record.org_id,
                    pipeline_id=record.pipeline_id,
                ).first()
            except (ValidationError, ValueError):
                stage = None
            if stage is None:
                return {"stage": [NOT_A_STAGE]}
            data = {**data, "stage": stage.code}
        return update_deal(request, record, data)
