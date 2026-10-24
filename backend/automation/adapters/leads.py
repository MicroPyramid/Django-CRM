from dataclasses import replace

from automation.objects import Adapter, Choice, FieldSpec, model_choices
from leads.models import Lead, LeadStage
from leads.sources import org_sources
from leads.updates import update_lead
from webhooks.events import lead_data


def source_choices(org):
    """The org's lead sources. A retired one can still be matched on, since
    records keep it, but a rule cannot set it."""
    return tuple(
        Choice(s.key, s.label, settable=s.is_active)
        for s in org_sources(org, create=False)
    )


class LeadAdapter(Adapter):
    route = "/leads/{id}"
    FIELDS = (
        FieldSpec("title", "Title", "text"),
        FieldSpec("first_name", "First name", "text"),
        FieldSpec("last_name", "Last name", "text"),
        FieldSpec("email", "Email", "text"),
        FieldSpec("phone", "Phone", "text"),
        FieldSpec("company_name", "Company", "text"),
        FieldSpec("job_title", "Job title", "text"),
        FieldSpec("website", "Website", "text"),
        FieldSpec("city", "City", "text"),
        FieldSpec("country", "Country", "choice", model_choices(Lead, "country")),
        # Conversion creates an account, contact and deal, so it is never an edit.
        FieldSpec(
            "status",
            "Status",
            "choice",
            model_choices(Lead, "status", unsettable={"converted"}),
        ),
        FieldSpec("source", "Source", "choice"),
        FieldSpec("industry", "Industry", "choice", model_choices(Lead, "industry")),
        FieldSpec("rating", "Rating", "choice", model_choices(Lead, "rating")),
        FieldSpec("stage", "Stage", "choice", settable=False),
        FieldSpec("opportunity_amount", "Estimated value", "number"),
        FieldSpec("probability", "Probability", "number"),
        FieldSpec("close_date", "Expected close date", "date"),
        FieldSpec("next_follow_up", "Next follow-up", "date"),
        FieldSpec("assigned_to", "Assigned to", "people"),
    )

    def own_fields(self, org):
        stages = tuple(
            Choice(str(stage.pk), stage.name, stage.pipeline.name)
            for stage in LeadStage.objects.filter(
                org=org, pipeline__org=org, pipeline__is_active=True
            )
            .select_related("pipeline")
            .order_by("-pipeline__is_default", "pipeline__name", "order")
        )
        choices = {"stage": stages, "source": source_choices(org)}
        return [
            replace(s, choices=choices[s.key]) if s.key in choices else s
            for s in self.FIELDS
        ]

    def read(self, record, key):
        if key == "stage":
            return str(record.stage_id) if record.stage_id else None
        return super().read(record, key)

    def name(self, record):
        full = f"{record.first_name or ''} {record.last_name or ''}".strip()
        return record.title or full or record.email or "Untitled lead"

    def task_parent(self, record):
        return {"lead": str(record.pk)}

    def webhook_data(self, record):
        return lead_data(record)

    def update(self, request, record, data):
        return update_lead(request, record, data)
