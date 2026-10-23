/// App Routes
class AppRoutes {
  AppRoutes._();

  // Auth routes
  static const String splash = '/splash';
  static const String login = '/login';
  static const String magicLinkEmail = '/magic-link/email';
  static const String magicLinkCode = '/magic-link/code';
  static const String orgSelection = '/org-selection';
  static const String orgCreate = '/org-selection/new';

  /// The first screen after creating a workspace: import contacts or leads
  /// from a spreadsheet, or skip. The web's `/welcome`. Also where the
  /// dashboard's card sends a workspace that is still empty.
  static const String importWelcome = '/welcome/import';

  // Main routes
  static const String dashboard = '/dashboard';
  static const String leads = '/leads';
  static const String leadDetail = '/leads/:id';
  static const String leadCreate = '/leads/create';
  static const String leadBoard = '/leads/board';
  static const String leadEdit = '/leads/:id/edit';
  static const String deals = '/deals';
  static const String dealDetail = '/deals/:id';
  static const String dealCreate = '/deals/create';
  static const String tickets = '/tickets';
  static const String ticketDetail = '/tickets/:id';
  static const String ticketCreate = '/tickets/create';
  static const String ticketEdit = '/tickets/:id/edit';
  static const String tasks = '/tasks';
  static const String taskBoard = '/tasks/board';
  static const String taskDetail = '/tasks/:id';
  static const String taskCreate = '/tasks/create';
  static const String taskEdit = '/tasks/:id/edit';
  static const String accounts = '/accounts';
  static const String accountCreate = '/accounts/create';
  static const String accountDetail = '/accounts/:id';
  static const String accountEdit = '/accounts/:id/edit';
  static const String accountStatement = '/accounts/:id/statement';
  static const String contacts = '/contacts';
  static const String contactCreate = '/contacts/create';
  static const String contactDetail = '/contacts/:id';
  static const String contactEdit = '/contacts/:id/edit';

  /// Side-by-side merge of two leads, contacts or accounts (G19):
  /// `/merge/contacts/<id>?with=<other id>`.
  static const String mergeCompare = '/merge/:module/:id';
  static const String more = '/more';
  static const String profile = '/more/profile';
  static const String team = '/more/team';

  /// The org settings cluster. Two segments deep under `/more`, matching
  /// `profile` and `team`, so nothing here can be mistaken for a record id the
  /// way `/invoices/estimates` once could.
  static const String settings = '/more/settings';
  static const String settingsCustomFields = '/more/settings/custom-fields';
  static const String settingsMacros = '/more/settings/macros';
  static const String settingsTags = '/more/settings/tags';
  static const String settingsLeadPipelines = '/more/settings/lead-pipelines';
  static const String settingsLeadPipelineDetail =
      '/more/settings/lead-pipelines/:pipelineId';

  static String settingsLeadPipeline(String id) =>
      '/more/settings/lead-pipelines/$id';

  static const String settingsDealPipelines = '/more/settings/deal-pipelines';
  static const String settingsDealPipelineDetail =
      '/more/settings/deal-pipelines/:pipelineId';

  static String settingsDealPipeline(String id) =>
      '/more/settings/deal-pipelines/$id';

  static const String settingsRouting = '/more/settings/routing';
  static const String settingsEscalation = '/more/settings/escalation';
  static const String settingsBusinessHours = '/more/settings/business-hours';
  static const String settingsReopen = '/more/settings/reopen';
  static const String settingsHelpCenter = '/more/settings/help-center';
  static const String settingsInboundEmail = '/more/settings/inbound-email';
  static const String settingsTicketApprovals =
      '/more/settings/ticket-approvals';
  static const String settingsApiTokens = '/more/settings/api-tokens';
  static const String settingsWebForms = '/more/settings/web-forms';

  /// Custom objects. `new` is declared before `:id` in the router.
  static const String objectRecordsPattern = '/more/objects/:key';
  static const String objectRecordCreatePattern = '/more/objects/:key/new';
  static const String objectRecordPattern = '/more/objects/:key/:id';
  static const String objectRecordEditPattern = '/more/objects/:key/:id/edit';
  static const String settingsObjects = '/more/settings/objects';
  static const String settingsObjectPattern = '/more/settings/objects/:key';

  static String objectRecords(String key) =>
      '/more/objects/${Uri.encodeComponent(key)}';
  static String objectRecordCreate(String key) => '${objectRecords(key)}/new';
  static String objectRecord(String key, String id) =>
      '${objectRecords(key)}/${Uri.encodeComponent(id)}';
  static String objectRecordEdit(String key, String id) =>
      '${objectRecord(key, id)}/edit';
  static String settingsObject(String key) =>
      '$settingsObjects/${Uri.encodeComponent(key)}';

  /// One form's editor. The id is a UUID the embed hands to every visitor
  /// by design, so it is an identifier rather than a secret; the org filter
  /// and the admin check on the endpoints behind it are the controls.
  static const String settingsWebFormDetail =
      '/more/settings/web-forms/:formId';

  static String settingsWebForm(String id) => '/more/settings/web-forms/$id';

  /// Outbound webhooks. Admin-only to read; the screens say so to a member.
  static const String settingsWebhooks = '/more/settings/webhooks';
  static const String settingsWebhookDetail =
      '/more/settings/webhooks/:webhookId';

  static String settingsWebhook(String id) => '/more/settings/webhooks/$id';

  /// The automation builder. Admin-only; the screens say so to a member.
  static const String settingsAutomation = '/more/settings/automation';
  static const String settingsAutomationNew = '/more/settings/automation/new';
  static const String settingsAutomationRuleDetail =
      '/more/settings/automation/:ruleId';
  static const String settingsAutomationRunsDetail =
      '/more/settings/automation/:ruleId/runs';

  static String settingsAutomationRule(String id) =>
      '/more/settings/automation/$id';

  static String settingsAutomationRuns(String id) =>
      '/more/settings/automation/$id/runs';

  /// The security audit log. Admin-only to read; the screen says so to a
  /// member.
  static const String settingsAuditLog = '/more/settings/audit-log';

  /// Your OWN tokens, under profile rather than under settings. Settings
  /// holds the admin's org-wide oversight list, which 403s a member; this
  /// is the self-scoped half every member may use.
  static const String profileTokens = '/more/profile/tokens';

  /// Your own task calendar feed, beside your tokens under profile.
  static const String profileCalendarFeed = '/more/profile/calendar-feed';
  static const String settingsOrganization = '/more/settings/organization';

  /// Which modules the organization uses. Admin only; the screen says so to a
  /// member.
  static const String settingsModules = '/more/settings/modules';
  static const String settingsOrganizationEdit =
      '/more/settings/organization/edit';

  /// Your own week of logged time. Not under `/more`: it is a workspace
  /// destination reached from the dashboard as often as from the menu, and a
  /// path that says where it lives is the one that survives being linked to.
  static const String timesheet = '/timesheet';

  /// Totals over a window, grouped. Nested under the timesheet on both
  /// clients, because it is the same entries asked a different question.
  static const String timeReport = '/timesheet/report';

  /// The notification feed. Matches the web app's `/notifications`.
  static const String notifications = '/notifications';

  /// Shared files. Matches the web app's `/documents`. There is no detail
  /// route on either client: the list says everything a document row holds,
  /// and the edit form is where the writes live.
  static const String documents = '/documents';
  static const String documentNew = '/documents/new';
  static const String documentEdit = '/documents/:id/edit';

  static String documentEditFor(String id) => '/documents/$id/edit';

  /// Sales goals. Matches the web app's `/goals`. Same shape as documents,
  /// and for the same reason.
  static const String goals = '/goals';
  static const String goalNew = '/goals/new';

  /// Finished periods and what each attained. Matches the web `/goals/history`.
  static const String goalHistory = '/goals/history';
  static const String goalEdit = '/goals/:id/edit';

  static String goalEditFor(String id) => '/goals/$id/edit';

  /// Help: product support from the BottleCRM team. The URL says help, the
  /// API behind it is `/api/support/`, and the screens keep the support name.
  /// Separate from CRM customer tickets, which live at `/tickets`.
  static const String help = '/help';
  static const String helpNew = '/help/new';
  static const String helpDetail = '/help/:id';

  /// Invoices. Matches the web app's `/invoices` and `/invoices/[id]`.
  static const String invoices = '/invoices';
  static const String invoiceDetail = '/invoices/:id';

  /// The sibling pages under invoices, matching the web's own paths. Declared
  /// BEFORE `invoiceDetail` in the route table: `/invoices/:id` would swallow
  /// every one of these as an id otherwise.
  static const String invoiceNew = '/invoices/new';
  static const String recurringNew = '/invoices/recurring/new';
  static const String estimates = '/invoices/estimates';

  /// The estimate form. Pass the `Deal` it starts from as `extra`, or nothing
  /// for a blank one.
  static const String estimateNew = '/invoices/estimates/new';
  static const String recurring = '/invoices/recurring';
  static const String products = '/invoices/products';
  static const String invoiceTemplates = '/invoices/templates';
  static const String invoiceTemplateNew = '/invoices/templates/new';
  static const String invoiceTemplateEdit = '/invoices/templates/:id/edit';
  static const String invoiceReports = '/invoices/reports';

  static String invoiceTemplateEditFor(String id) =>
      '/invoices/templates/$id/edit';

  // Knowledge base
  static const String solutions = '/solutions';
  static const String solutionNew = '/solutions/new';
  static const String solutionDetail = '/solutions/:id';

  // Approvals
  static const String approvalsInbox = '/tickets/approvals';

  // Analytics
  static const String ticketAnalytics = '/tickets/analytics';

  // Ticket board, by status or by one pipeline's stages
  static const String ticketBoard = '/tickets/board';

  /// Values for the `?view=` parameter on the leads and tasks lists. Each one
  /// opens the list already narrowed to what one dashboard badge counted, so
  /// the badge and the list it opens agree on a number. The filter itself is
  /// built by `TaskFilters` / `LeadFilters`, which is where the definition
  /// lives; these are just the names carried through the URL.
  static const String viewOverdue = 'overdue';
  static const String viewDueToday = 'due-today';
  static const String viewFollowUps = 'follow-ups';
  static const String viewHot = 'hot';
}
