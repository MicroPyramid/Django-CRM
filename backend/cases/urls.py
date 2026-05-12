from django.urls import path

from cases import (
    analytics_views,
    approval_views,
    bulk_views,
    csat_views,
    escalation_views,
    import_views,
    inbound_views,
    kanban_views,
    kb_views,
    merge_views,
    parent_views,
    unmerge_views,
    routing_views,
    solution_views,
    time_views,
    views,
    watcher_views,
)

app_name = "api_cases"

urlpatterns = [
    # Cases list endpoint
    path("", views.CaseListView.as_view()),
    # Kanban endpoints (must be before <str:pk>/ to avoid conflicts)
    path("kanban/", kanban_views.CaseKanbanView.as_view(), name="case_kanban"),
    # Pipeline management
    path(
        "pipelines/",
        kanban_views.CasePipelineListCreateView.as_view(),
        name="pipeline_list_create",
    ),
    path(
        "pipelines/<str:pk>/",
        kanban_views.CasePipelineDetailView.as_view(),
        name="pipeline_detail",
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/",
        kanban_views.CaseStageCreateView.as_view(),
        name="stage_create",
    ),
    path(
        "pipelines/<str:pipeline_pk>/stages/reorder/",
        kanban_views.CaseStageReorderView.as_view(),
        name="stage_reorder",
    ),
    # Stage management
    path(
        "stages/<str:pk>/",
        kanban_views.CaseStageDetailView.as_view(),
        name="stage_detail",
    ),
    # Solutions (Knowledge Base) endpoints (must be before <str:pk>/ to avoid conflicts)
    path(
        "solutions/", solution_views.SolutionListView.as_view(), name="solutions_list"
    ),
    path(
        "solutions/<str:pk>/",
        solution_views.SolutionDetailView.as_view(),
        name="solution_detail",
    ),
    path(
        "solutions/<str:pk>/publish/",
        solution_views.SolutionPublishView.as_view(),
        name="solution_publish",
    ),
    path(
        "solutions/<str:pk>/unpublish/",
        solution_views.SolutionUnpublishView.as_view(),
        name="solution_unpublish",
    ),
    # Reopen policy (admin singleton, must be before <str:pk>/ patterns)
    path(
        "reopen-policy/",
        views.ReopenPolicyView.as_view(),
        name="reopen_policy",
    ),
    # Escalation policies (admin CRUD, must be before <str:pk>/ patterns)
    path(
        "escalation-policies/",
        escalation_views.EscalationPolicyListCreateView.as_view(),
        name="escalation_policy_list_create",
    ),
    path(
        "escalation-policies/<str:pk>/",
        escalation_views.EscalationPolicyDetailView.as_view(),
        name="escalation_policy_detail",
    ),
    # Routing rules (admin CRUD + dry-run test endpoint, must be before <str:pk>/ patterns)
    path(
        "routing-rules/",
        routing_views.RoutingRuleListCreateView.as_view(),
        name="routing_rule_list_create",
    ),
    path(
        "routing-rules/<str:pk>/",
        routing_views.RoutingRuleDetailView.as_view(),
        name="routing_rule_detail",
    ),
    path(
        "routing-rules/<str:pk>/test/",
        routing_views.RoutingRuleTestView.as_view(),
        name="routing_rule_test",
    ),
    # Inbound email — public webhook (SNS-signed) + admin mailbox CRUD.
    path(
        "inbound/<str:mailbox_id>/",
        inbound_views.InboundMailboxWebhookView.as_view(),
        name="inbound_webhook",
    ),
    path(
        "mailboxes/",
        inbound_views.InboundMailboxListCreateView.as_view(),
        name="inbound_mailbox_list_create",
    ),
    path(
        "mailboxes/<str:pk>/",
        inbound_views.InboundMailboxDetailView.as_view(),
        name="inbound_mailbox_detail",
    ),
    # Watching list (must be before <str:pk>/ patterns)
    path(
        "watching/",
        watcher_views.WatchingListView.as_view(),
        name="cases_watching",
    ),
    # Analytics dashboards (must be before <str:pk>/ patterns)
    path(
        "analytics/frt/",
        analytics_views.AnalyticsFrtView.as_view(),
        name="analytics_frt",
    ),
    path(
        "analytics/mttr/",
        analytics_views.AnalyticsMttrView.as_view(),
        name="analytics_mttr",
    ),
    path(
        "analytics/backlog/",
        analytics_views.AnalyticsBacklogView.as_view(),
        name="analytics_backlog",
    ),
    path(
        "analytics/agents/",
        analytics_views.AnalyticsAgentsView.as_view(),
        name="analytics_agents",
    ),
    path(
        "analytics/sla/",
        analytics_views.AnalyticsSlaView.as_view(),
        name="analytics_sla",
    ),
    path(
        "analytics/drilldown/",
        analytics_views.AnalyticsDrilldownView.as_view(),
        name="analytics_drilldown",
    ),
    path(
        "analytics/export/",
        analytics_views.AnalyticsExportView.as_view(),
        name="analytics_export",
    ),
    # CSAT aggregate (must be before <str:pk>/ patterns)
    path(
        "csat/aggregate/",
        csat_views.CsatAggregateView.as_view(),
        name="csat_aggregate",
    ),
    # Bulk endpoints (must be before <str:pk>/ patterns)
    path(
        "bulk/update/",
        bulk_views.BulkUpdateCasesView.as_view(),
        name="cases_bulk_update",
    ),
    path(
        "bulk/delete/",
        bulk_views.BulkDeleteCasesView.as_view(),
        name="cases_bulk_delete",
    ),
    # CSV import (must be before <str:pk>/ patterns)
    path(
        "import/preview/",
        import_views.CaseImportPreviewView.as_view(),
        name="cases_import_preview",
    ),
    path(
        "import/commit/",
        import_views.CaseImportCommitView.as_view(),
        name="cases_import_commit",
    ),
    # Case ↔ Solution linking (M2M endpoints — must be before <str:pk>/ patterns)
    path(
        "<str:pk>/solutions/",
        views.CaseSolutionLinkView.as_view(),
        name="case_solution_link",
    ),
    path(
        "<str:pk>/solutions/<str:solution_pk>/",
        views.CaseSolutionLinkView.as_view(),
        name="case_solution_unlink",
    ),
    # Audit-log feed (must be before <str:pk>/ pattern)
    path(
        "<str:pk>/activities/",
        views.CaseActivityListView.as_view(),
        name="case_activities",
    ),
    # KB suggester typeahead (must be before <str:pk>/ pattern)
    path(
        "<str:pk>/solution-suggestions/",
        kb_views.SolutionSuggestionsView.as_view(),
        name="case_solution_suggestions",
    ),
    # Watch toggle + watchers list (must be before <str:pk>/ pattern)
    path(
        "<str:pk>/watch/",
        watcher_views.WatchView.as_view(),
        name="case_watch",
    ),
    path(
        "<str:pk>/watchers/",
        watcher_views.WatchersListView.as_view(),
        name="case_watchers",
    ),
    # Merge endpoint (must be before <str:pk>/ pattern)
    path(
        "<str:pk>/merge/<str:into_id>/",
        merge_views.CaseMergeView.as_view(),
        name="case_merge",
    ),
    path(
        "<str:pk>/unmerge/",
        unmerge_views.CaseUnmergeView.as_view(),
        name="case_unmerge",
    ),
    # Parent/child tree endpoints (must be before <str:pk>/ pattern)
    path(
        "<str:pk>/tree/",
        parent_views.CaseTreeView.as_view(),
        name="case_tree",
    ),
    path(
        "<str:pk>/link/",
        parent_views.CaseLinkParentView.as_view(),
        name="case_link_parent",
    ),
    path(
        "<str:pk>/close-with-children/",
        parent_views.CaseCloseWithChildrenView.as_view(),
        name="case_close_with_children",
    ),
    # Time-tracking endpoints (must be before <str:pk>/ catchall)
    path(
        "<str:pk>/time-entries/",
        time_views.TimeEntryListCreateView.as_view(),
        name="case_time_entries",
    ),
    path(
        "<str:pk>/time-entries/start/",
        time_views.TimeEntryStartView.as_view(),
        name="case_time_entry_start",
    ),
    path(
        "<str:pk>/time-summary/",
        time_views.TimeSummaryView.as_view(),
        name="case_time_summary",
    ),
    # Approval workflows (must be before <str:pk>/ catchall) — Tier 3 approvals.
    path(
        "approval-rules/",
        approval_views.ApprovalRuleListCreateView.as_view(),
        name="approval_rule_list_create",
    ),
    path(
        "approval-rules/<str:pk>/",
        approval_views.ApprovalRuleDetailView.as_view(),
        name="approval_rule_detail",
    ),
    path(
        "approvals/",
        approval_views.ApprovalInboxView.as_view(),
        name="approval_inbox",
    ),
    path(
        "approvals/<str:pk>/approve/",
        approval_views.ApprovalApproveView.as_view(),
        name="approval_approve",
    ),
    path(
        "approvals/<str:pk>/reject/",
        approval_views.ApprovalRejectView.as_view(),
        name="approval_reject",
    ),
    path(
        "approvals/<str:pk>/cancel/",
        approval_views.ApprovalCancelView.as_view(),
        name="approval_cancel",
    ),
    path(
        "<str:pk>/request-approval/",
        approval_views.CaseRequestApprovalView.as_view(),
        name="case_request_approval",
    ),
    # Case detail routes (must be after all named routes due to <str:pk> pattern)
    path("<str:pk>/", views.CaseDetailView.as_view()),
    path("<str:pk>/move/", kanban_views.CaseMoveView.as_view(), name="case_move"),
    path("comment/<str:pk>/", views.CaseCommentView.as_view()),
    path("attachment/<str:pk>/", views.CaseAttachmentView.as_view()),
]
