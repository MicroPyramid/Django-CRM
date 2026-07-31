from datetime import date, timedelta

from django.db.models import DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Account
from accounts.serializer import AccountSerializer
from cases.models import Case
from common import serializer, swagger_params
from common.models import Activity
from common.permissions import HasOrgContext
from common.utils import STAGES
from contacts.models import Contact
from contacts.serializer import ContactSerializer
from invoices.models import UNPAID_STATUSES, Invoice
from leads.models import Lead
from leads.serializer import LeadSerializer
from opportunity.models import Opportunity, StageAgingConfig
from opportunity.serializer import OpportunitySerializer
from opportunity.workflow import DEFAULT_STAGE_EXPECTED_DAYS, ROTTEN_MULTIPLIER
from tasks.models import Task
from tasks.serializer import TaskSerializer

# Sales stages a deal can still be worked (and therefore "age") in — mirrors
# the open-stage list ApiHomeView uses for its revenue metrics.
OPEN_STAGES = ["PROSPECTING", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]

# Case statuses that are still open. The rest (Closed, Rejected, Duplicate) are
# terminal; listing the open ones explicitly means a new terminal status is a
# deliberate edit here, not a silent inclusion in the "needs a reply" queue.
OPEN_CASE_STATUSES = ["New", "Assigned", "Pending"]

_CURRENCY_SYMBOL = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "AUD": "A$",
    "CAD": "C$",
}


def _fmt_money(amount, currency):
    """One-line money for a human sentence, e.g. '$42,000'. Falls back to
    'CODE 42,000' for currencies without a symbol. Formatting lives here only
    because the Today queue ships each row as one prebuilt line; every other
    endpoint returns structured numbers and lets the client format them."""
    n = float(amount or 0)
    sym = _CURRENCY_SYMBOL.get((currency or "").upper())
    return f"{sym}{n:,.0f}" if sym else f"{(currency or '').upper()} {n:,.0f}".strip()


def _fmt_date(d):
    """'Jul 5' — portable (avoids the platform-specific %-d)."""
    return f"{d:%b} {d.day}"


class ApiHomeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["home"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="ApiHomeResponse",
                fields={
                    "accounts_count": serializers.IntegerField(),
                    "contacts_count": serializers.IntegerField(),
                    "leads_count": serializers.IntegerField(),
                    "opportunities_count": serializers.IntegerField(),
                    "accounts": AccountSerializer(many=True),
                    "contacts": ContactSerializer(many=True),
                    "leads": LeadSerializer(many=True),
                    "opportunities": OpportunitySerializer(many=True),
                },
            )
        },
    )
    def get(self, request, format=None):
        org = request.profile.org
        profile = request.profile
        today = date.today()

        accounts = Account.objects.filter(is_active=True, org=org)
        contacts = Contact.objects.filter(org=org)
        leads = Lead.objects.filter(org=org).exclude(
            Q(status="converted") | Q(status="closed")
        )
        opportunities = Opportunity.objects.filter(org=org)
        tasks = Task.objects.filter(org=org)

        is_admin = profile.role == "ADMIN" or request.user.is_superuser

        if not is_admin:
            accounts = accounts.filter(
                Q(assigned_to=profile) | Q(created_by=profile.user)
            )
            contacts = contacts.filter(
                Q(assigned_to__id__in=[profile.id]) | Q(created_by=profile.user)
            )
            leads = leads.filter(
                Q(assigned_to__id__in=[profile.id]) | Q(created_by=profile.user)
            ).exclude(status="closed")
            opportunities = opportunities.filter(
                Q(assigned_to__id__in=[profile.id]) | Q(created_by=profile.user)
            )
            tasks = tasks.filter(
                Q(assigned_to__id__in=[profile.id]) | Q(created_by=profile.user)
            )

        # Build base context (existing)
        context = {}
        context["accounts_count"] = accounts.count()
        context["contacts_count"] = contacts.count()
        context["leads_count"] = leads.count()
        context["opportunities_count"] = opportunities.count()
        context["accounts"] = AccountSerializer(accounts, many=True).data
        context["contacts"] = ContactSerializer(contacts, many=True).data
        context["leads"] = LeadSerializer(leads, many=True).data
        context["opportunities"] = OpportunitySerializer(opportunities, many=True).data

        # NEW: Urgent counts for Focus Bar
        overdue_tasks = tasks.filter(
            status__in=["New", "In Progress"], due_date__lt=today
        ).count()

        tasks_due_today = tasks.filter(
            status__in=["New", "In Progress"], due_date=today
        ).count()

        followups_today = leads.filter(next_follow_up=today).count()

        hot_leads = leads.filter(
            rating="HOT", status__in=["assigned", "in process"]
        ).count()

        context["urgent_counts"] = {
            "overdue_tasks": overdue_tasks,
            "tasks_due_today": tasks_due_today,
            "followups_today": followups_today,
            "hot_leads": hot_leads,
        }

        # Get org's default currency for filtering
        org_currency = org.default_currency or "USD"

        # NEW: Pipeline by stage (filtered by org's default currency)
        # Only sum amounts that match org's currency for accurate totals
        pipeline_by_stage = {}
        for stage_code, stage_label in STAGES:
            stage_opps = opportunities.filter(stage=stage_code)
            # Filter by currency for value calculation (include null as matching org currency)
            stage_opps_with_currency = stage_opps.filter(
                Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
            )
            stage_value = stage_opps_with_currency.aggregate(
                total=Coalesce(Sum("amount"), 0, output_field=DecimalField())
            )["total"]
            pipeline_by_stage[stage_code] = {
                "count": stage_opps.count(),  # Count all opportunities
                "value": float(stage_value or 0),  # Value only for matching currency
                "label": stage_label,
            }
        context["pipeline_by_stage"] = pipeline_by_stage

        # NEW: Revenue metrics (filtered by org's default currency)
        open_stages = ["PROSPECTING", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]
        open_opps = opportunities.filter(stage__in=open_stages)
        # Filter by currency for value calculations
        open_opps_with_currency = open_opps.filter(
            Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
        )

        pipeline_value = open_opps_with_currency.aggregate(
            total=Coalesce(Sum("amount"), 0, output_field=DecimalField())
        )["total"]

        # Weighted pipeline = sum of (amount * probability / 100)
        weighted_pipeline = open_opps_with_currency.aggregate(
            total=Coalesce(
                Sum(F("amount") * F("probability") / 100),
                0,
                output_field=DecimalField(),
            )
        )["total"]

        # Won this month (use timezone-aware datetime for updated_at comparison)
        now = timezone.now()
        first_day_of_month = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        won_opps = opportunities.filter(
            stage="CLOSED_WON", updated_at__gte=first_day_of_month
        )
        won_opps_with_currency = won_opps.filter(
            Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
        )
        won_this_month = won_opps_with_currency.aggregate(
            total=Coalesce(Sum("amount"), 0, output_field=DecimalField())
        )["total"]

        # Conversion rate: leads converted / total leads
        total_leads_all = Lead.objects.filter(org=org).count()
        converted_leads = Lead.objects.filter(org=org, status="converted").count()
        conversion_rate = (
            (converted_leads / total_leads_all * 100) if total_leads_all > 0 else 0
        )

        # Count opportunities in other currencies (for info)
        other_currency_count = opportunities.exclude(
            Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
        ).count()

        context["revenue_metrics"] = {
            "pipeline_value": float(pipeline_value or 0),
            "weighted_pipeline": float(weighted_pipeline or 0),
            "won_this_month": float(won_this_month or 0),
            "conversion_rate": round(conversion_rate, 1),
            "currency": org_currency,
            "other_currency_count": other_currency_count,
        }

        # NEW: Hot leads list for dedicated panel
        hot_leads_qs = leads.filter(
            rating="HOT", status__in=["assigned", "in process"]
        ).order_by("-created_at")[:10]

        context["hot_leads"] = [
            {
                "id": str(lead.id),
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company_name,
                "rating": lead.rating,
                "next_follow_up": (
                    lead.next_follow_up.isoformat() if lead.next_follow_up else None
                ),
                "last_contacted": (
                    lead.last_contacted.isoformat() if lead.last_contacted else None
                ),
            }
            for lead in hot_leads_qs
        ]

        # Include tasks in dashboard response (avoid separate API call)
        upcoming_tasks = tasks.filter(
            status__in=["New", "In Progress"], due_date__isnull=False
        ).order_by("due_date")[:10]
        context["tasks"] = TaskSerializer(upcoming_tasks, many=True).data

        # Goal summary for current user
        from opportunity.models import SalesGoal

        goal_filter = Q(assigned_to=profile) | Q(team__in=profile.user_teams.all())
        if is_admin:
            goal_filter |= Q(assigned_to__isnull=True, team__isnull=True)

        active_goals = (
            SalesGoal.objects.filter(
                org=org,
                is_active=True,
                period_start__lte=today,
                period_end__gte=today,
            )
            .filter(goal_filter)
            .distinct()[:3]
        )
        context["goal_summary"] = [
            {
                "id": str(g.id),
                "name": g.name,
                "goal_type": g.goal_type,
                "target_value": float(g.target_value),
                "progress_value": float(g.compute_progress()),
                "progress_percent": g.progress_percent,
                "status": g.status,
            }
            for g in active_goals
        ]

        # Include recent activities (avoid separate API call)
        activities = (
            Activity.objects.filter(org=org)
            .select_related("user", "user__user")
            .order_by("-created_at")[:10]
        )
        context["activities"] = serializer.ActivitySerializer(
            activities, many=True
        ).data

        return Response(context, status=status.HTTP_200_OK)


class ApiTodayView(APIView):
    """The v2 home ("Today"): one prioritised, cross-model action queue.

    This is NOT the KPI dashboard (that is ``ApiHomeView`` at
    ``/api/dashboard/``). It answers "what wants me right now" by folding four
    sources into a single ranked list:

      * support cases still awaiting a first response (SLA-breached first),
      * invoices past their due date and still unpaid,
      * open deals that have gone quiet (stage-aging yellow/red),
      * tasks overdue or due today.

    Security: every query is org-scoped — the org comes from the JWT via
    middleware, never the client — and a member sees only rows assigned to or
    created by them, the same visibility ``ApiHomeView`` applies. Admins see the
    whole org. ``HasOrgContext`` guarantees ``request.profile``/``org`` are set,
    so this never dereferences a ``None`` profile.
    """

    permission_classes = (IsAuthenticated, HasOrgContext)

    @extend_schema(
        tags=["home"],
        parameters=swagger_params.organization_params,
        responses={
            200: inline_serializer(
                name="ApiTodayResponse",
                fields={
                    "queue": serializers.ListField(child=serializers.DictField()),
                    "summary": inline_serializer(
                        name="ApiTodaySummary",
                        fields={
                            "count": serializers.IntegerField(),
                            "quiet_deals": serializers.IntegerField(),
                            "quiet_value": serializers.FloatField(),
                            "cleared_yesterday": serializers.IntegerField(),
                        },
                    ),
                    "later": serializers.ListField(child=serializers.DictField()),
                },
            )
        },
    )
    def get(self, request, format=None):
        org = request.profile.org
        profile = request.profile
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_end = today + timedelta(days=7)
        is_admin = profile.role == "ADMIN" or request.user.is_superuser
        org_currency = org.default_currency or "USD"

        def mine(qs):
            """Restrict a queryset to rows a member may see. ``created_by`` is a
            User FK (compared to ``profile.user``); ``assigned_to`` is an M2M of
            Profile — the OR-over-a-join can duplicate rows, so distinct()."""
            return qs.filter(
                Q(assigned_to__id__in=[profile.id]) | Q(created_by=profile.user)
            ).distinct()

        # ── base, org-scoped querysets ──────────────────────────────────────
        opportunities = Opportunity.objects.filter(org=org, stage__in=OPEN_STAGES)
        cases = Case.objects.filter(org=org, status__in=OPEN_CASE_STATUSES)
        invoices = Invoice.objects.filter(
            org=org, status__in=UNPAID_STATUSES, due_date__lt=today
        )
        tasks = Task.objects.filter(
            org=org, status__in=["New", "In Progress"], due_date__lte=today
        )
        if not is_admin:
            opportunities = mine(opportunities)
            cases = mine(cases)
            invoices = mine(invoices)
            tasks = mine(tasks)

        # ── deal aging as DB date cutoffs (no per-row Python) ───────────────
        # For each open stage: "quiet" (yellow+) once the deal has sat past its
        # yellow threshold; "rotten" (red) at 1.5x expected. Translating the
        # thresholds to stage_changed_at cutoffs keeps this a filter, not a scan.
        aging_configs = {
            c.stage: c
            for c in StageAgingConfig.objects.filter(org=org, stage__in=OPEN_STAGES)
        }
        quiet_q = None
        rotten_cutoffs = {}
        for stage in OPEN_STAGES:
            cfg = aging_configs.get(stage)
            expected = (
                cfg.expected_days if cfg else DEFAULT_STAGE_EXPECTED_DAYS.get(stage)
            )
            if not expected:
                continue
            warning = cfg.warning_days if cfg else None
            yellow_days = min(warning, expected) if warning else expected
            yellow_cutoff = now - timedelta(days=yellow_days)
            rotten_cutoffs[stage] = now - timedelta(days=expected * ROTTEN_MULTIPLIER)
            clause = Q(stage=stage, stage_changed_at__lte=yellow_cutoff)
            quiet_q = clause if quiet_q is None else (quiet_q | clause)

        quiet_opps = (
            opportunities.filter(quiet_q)
            if quiet_q is not None
            else opportunities.none()
        )
        quiet_deals = quiet_opps.count()
        quiet_value = quiet_opps.filter(
            Q(currency=org_currency) | Q(currency__isnull=True) | Q(currency="")
        ).aggregate(total=Coalesce(Sum("amount"), 0, output_field=DecimalField()))[
            "total"
        ]

        # ── build the queue (each source pre-ordered by urgency, capped) ────
        queue = []

        # 1. Cases awaiting a first response. SLA-breached outrank in-SLA ones;
        #    High/Urgent priority render with the alarm tone.
        for c in (
            cases.filter(first_response_at__isnull=True)
            .select_related("account")
            .order_by("created_at")[:25]
        ):
            deadline = c.created_at + timedelta(hours=c.sla_first_response_hours or 4)
            breached = deadline < now
            hot = c.priority in ("High", "Urgent")
            queue.append(
                {
                    "_rank": 0 if breached else 3,
                    "id": f"case-{c.id}",
                    "tone": "rust" if (hot or breached) else "clay",
                    "due": "Overdue" if breached else "Today",
                    "title": c.name,
                    "detail": f"{c.priority} · {c.account.name if c.account_id else 'No account'} · awaiting first reply",
                    "action": "Reply",
                    "href": f"/v2/tickets/{c.id}",
                }
            )

        # 2. Overdue invoices.
        for inv in invoices.select_related("account").order_by("due_date")[:25]:
            queue.append(
                {
                    "_rank": 1,
                    "id": f"invoice-{inv.id}",
                    "tone": "clay",
                    "due": "Overdue",
                    "title": inv.invoice_title or inv.invoice_number,
                    "detail": f"{_fmt_money(inv.total_amount, inv.currency)} · {inv.account.name if inv.account_id else 'No account'} · due {_fmt_date(inv.due_date)}",
                    "action": "Send a reminder",
                    "href": f"/v2/invoices/{inv.id}",
                }
            )

        # 3. Quiet deals (aging). Rotten (red) outrank merely slowing (yellow).
        stage_labels = dict(STAGES)
        for opp in quiet_opps.order_by("stage_changed_at")[:25]:
            rotten = (
                opp.stage in rotten_cutoffs
                and opp.stage_changed_at is not None
                and opp.stage_changed_at <= rotten_cutoffs[opp.stage]
            )
            days = (now - opp.stage_changed_at).days if opp.stage_changed_at else 0
            queue.append(
                {
                    "_rank": 2 if rotten else 6,
                    "id": f"deal-{opp.id}",
                    "tone": "rust" if rotten else "clay",
                    "due": "Stalled" if rotten else "Aging",
                    "title": opp.name,
                    "detail": f"No movement for {days} days · {_fmt_money(opp.amount, opp.currency)} · {stage_labels.get(opp.stage, opp.stage)}",
                    "action": "Open the deal",
                    "href": f"/v2/pipeline/{opp.id}",
                }
            )

        # 4. Tasks overdue or due today.
        for t in tasks.order_by("due_date")[:25]:
            overdue = t.due_date is not None and t.due_date < today
            queue.append(
                {
                    "_rank": 4 if overdue else 5,
                    "id": f"task-{t.id}",
                    "tone": "clay" if overdue else "slate",
                    "due": "Overdue" if overdue else "Today",
                    "title": t.title,
                    "detail": (
                        f"Due {_fmt_date(t.due_date)} · {t.priority}"
                        if t.due_date
                        else t.priority
                    ),
                    "action": "Open the task",
                    "href": f"/v2/tasks/{t.id}",
                }
            )

        queue.sort(key=lambda item: item["_rank"])
        total_urgent = len(queue)
        queue = [{k: v for k, v in item.items() if k != "_rank"} for item in queue[:8]]

        # ── "cleared yesterday" (a morale line) ─────────────────────────────
        # Tasks have no completed_at, so proxy with "marked Completed and last
        # touched yesterday"; cases carry a real closed_on date.
        cleared_tasks = Task.objects.filter(
            org=org, status="Completed", updated_at__date=yesterday
        )
        cleared_cases = Case.objects.filter(
            org=org, status="Closed", closed_on=yesterday
        )
        if not is_admin:
            cleared_tasks = mine(cleared_tasks)
            cleared_cases = mine(cleared_cases)

        summary = {
            "count": total_urgent,
            "quiet_deals": quiet_deals,
            "quiet_value": float(quiet_value or 0),
            "cleared_yesterday": cleared_tasks.count() + cleared_cases.count(),
        }

        # ── "later this week" (due tomorrow … +7 days) ──────────────────────
        soon = Q(due_date__gt=today, due_date__lte=week_end)
        later_tasks = Task.objects.filter(
            org=org, status__in=["New", "In Progress"]
        ).filter(soon)
        later_opps = Opportunity.objects.filter(
            org=org, stage__in=OPEN_STAGES, closed_on__gt=today, closed_on__lte=week_end
        )
        later_invoices = Invoice.objects.filter(
            org=org,
            status__in=UNPAID_STATUSES,
            due_date__gt=today,
            due_date__lte=week_end,
        )
        if not is_admin:
            later_tasks = mine(later_tasks)
            later_opps = mine(later_opps)
            later_invoices = mine(later_invoices)

        later_rows = []
        for t in later_tasks.order_by("due_date")[:10]:
            later_rows.append(
                (
                    t.due_date,
                    {
                        "id": f"task-{t.id}",
                        "day": t.due_date.strftime("%a"),
                        "title": t.title,
                        "meta": f"Task · {t.priority}",
                    },
                )
            )
        for o in later_opps.order_by("closed_on")[:10]:
            later_rows.append(
                (
                    o.closed_on,
                    {
                        "id": f"deal-{o.id}",
                        "day": o.closed_on.strftime("%a"),
                        "title": f"{o.name} expected to close",
                        "meta": f"{stage_labels.get(o.stage, o.stage)} · {_fmt_money(o.amount, o.currency)}",
                    },
                )
            )
        for inv in later_invoices.order_by("due_date")[:10]:
            later_rows.append(
                (
                    inv.due_date,
                    {
                        "id": f"invoice-{inv.id}",
                        "day": inv.due_date.strftime("%a"),
                        "title": f"{inv.invoice_title or inv.invoice_number} due",
                        "meta": _fmt_money(inv.total_amount, inv.currency),
                    },
                )
            )
        later_rows.sort(key=lambda r: r[0])
        later = [row for _, row in later_rows[:6]]

        return Response(
            {"queue": queue, "summary": summary, "later": later},
            status=status.HTTP_200_OK,
        )


class ActivityListView(APIView):
    """
    Get recent activities for the organization
    Returns the last 10 activities by default
    """

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["activities"],
        parameters=swagger_params.organization_params
        + [
            OpenApiParameter(
                name="limit",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of activities to return (default: 10, max: 50)",
            ),
            OpenApiParameter(
                name="entity_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by entity type (Account, Lead, Contact, etc.)",
            ),
        ],
        responses={200: serializer.ActivitySerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        if not request.profile:
            return Response(
                {"error": True, "errors": "Organization context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get query params
        limit = min(int(request.query_params.get("limit", 10)), 50)
        entity_type = request.query_params.get("entity_type", None)

        # Query activities for this organization
        queryset = Activity.objects.filter(org=request.profile.org)

        # Filter by entity type if specified
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        # Get most recent activities
        activities = queryset.select_related("user", "user__user")[:limit]

        # Serialize
        activities_data = serializer.ActivitySerializer(activities, many=True).data

        return Response(
            {
                "error": False,
                "count": len(activities_data),
                "activities": activities_data,
            },
            status=status.HTTP_200_OK,
        )
