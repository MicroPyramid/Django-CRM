import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../data/models/deal.dart' show Deal;
import '../providers/auth_provider.dart';
import '../providers/duplicates_provider.dart';
import '../widgets/common/module_gate.dart';
import 'app_routes.dart';

export 'app_routes.dart';
export 'record_routes.dart';

// Auth Screens
import '../screens/objects/object_record_detail_screen.dart';
import '../screens/objects/object_record_form_screen.dart';
import '../screens/objects/object_records_screen.dart';
import '../screens/auth/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/magic_link_email_screen.dart';
import '../screens/auth/magic_link_code_screen.dart';
import '../screens/accounts/account_detail_screen.dart';
import '../screens/accounts/account_form_screen.dart';
import '../screens/accounts/account_statement_screen.dart';
import '../screens/accounts/accounts_list_screen.dart';
import '../screens/auth/org_create_screen.dart';
import '../screens/contacts/contact_detail_screen.dart';
import '../screens/contacts/contact_form_screen.dart';
import '../screens/contacts/contacts_list_screen.dart';
import '../screens/duplicates/merge_compare_screen.dart';
import '../screens/onboarding/import_welcome_screen.dart';
import '../screens/auth/org_selection_screen.dart';

// Main Screens
import '../screens/dashboard/dashboard_screen.dart';
import '../screens/leads/leads_list_screen.dart';
import '../screens/leads/lead_detail_screen.dart';
import '../screens/leads/lead_create_screen.dart';
import '../screens/leads/lead_form_screen.dart';
import '../screens/leads/lead_board_screen.dart';
import '../screens/deals/deals_list_screen.dart';
import '../screens/deals/deal_detail_screen.dart';
import '../screens/deals/deal_form_screen.dart';
import '../screens/tickets/tickets_list_screen.dart';
import '../screens/tickets/ticket_detail_screen.dart';
import '../screens/tickets/ticket_create_screen.dart';
import '../screens/tickets/ticket_form_screen.dart';
import '../screens/tasks/board_screen.dart';
import '../screens/tasks/tasks_list_screen.dart';
import '../screens/tasks/task_detail_screen.dart';
import '../screens/tasks/task_form_screen.dart';
import '../screens/settings/custom_fields_screen.dart';
import '../screens/settings/macros_screen.dart';
import '../screens/settings/object_settings_screen.dart';
import '../screens/settings/objects_settings_screen.dart';
import '../screens/settings/modules_screen.dart';
import '../screens/settings/more_screen.dart';
import '../screens/settings/profile_screen.dart';
import '../screens/settings/api_tokens_screen.dart';
import '../screens/settings/calendar_feed_screen.dart';
import '../screens/settings/my_api_tokens_screen.dart';
import '../screens/settings/approval_rules_screen.dart';
import '../screens/settings/business_hours_screen.dart';
import '../screens/settings/escalation_screen.dart';
import '../screens/settings/inbound_email_screen.dart';
import '../screens/settings/deal_pipeline_detail_screen.dart';
import '../screens/settings/deal_pipelines_screen.dart';
import '../screens/settings/lead_pipeline_detail_screen.dart';
import '../screens/settings/lead_pipelines_screen.dart';
import '../screens/settings/organization_edit_screen.dart';
import '../screens/settings/organization_screen.dart';
import '../screens/settings/help_center_screen.dart';
import '../screens/settings/reopen_screen.dart';
import '../screens/settings/routing_screen.dart';
import '../screens/settings/settings_hub_screen.dart';
import '../screens/settings/tags_screen.dart';
import '../screens/settings/web_form_detail_screen.dart';
import '../screens/settings/web_forms_screen.dart';
import '../screens/settings/audit_log_screen.dart';
import '../screens/settings/automation/automation_runs_screen.dart';
import '../screens/settings/automation/automation_rule_screen.dart';
import '../screens/settings/automation/automation_rules_screen.dart';
import '../screens/settings/webhook_detail_screen.dart';
import '../screens/settings/webhooks_screen.dart';
import '../screens/settings/team_screen.dart';
import '../screens/solutions/solutions_list_screen.dart';
import '../screens/solutions/solution_detail_screen.dart';
import '../screens/tickets/approvals_inbox_screen.dart';
import '../screens/tickets/ticket_analytics_screen.dart';
import '../screens/tickets/ticket_board_screen.dart';
import '../screens/timesheet/time_report_screen.dart';
import '../screens/timesheet/timesheet_screen.dart';
import '../screens/notifications/notifications_screen.dart';
import '../screens/documents/documents_list_screen.dart';
import '../screens/documents/document_form_screen.dart';
import '../screens/goals/goals_screen.dart';
import '../screens/goals/goal_form_screen.dart';
import '../screens/goals/goal_history_screen.dart';
import '../screens/invoices/invoices_list_screen.dart';
import '../screens/invoices/invoice_detail_screen.dart';
import '../screens/invoices/estimates_list_screen.dart';
import '../screens/invoices/recurring_list_screen.dart';
import '../screens/invoices/products_list_screen.dart';
import '../screens/invoices/invoice_template_form_screen.dart';
import '../screens/invoices/invoice_templates_screen.dart';
import '../screens/invoices/invoice_reports_screen.dart';
import '../screens/invoices/new_estimate_screen.dart';
import '../screens/invoices/new_invoice_screen.dart';
import '../screens/invoices/new_recurring_screen.dart';
import '../screens/support/support_create_screen.dart';
import '../screens/support/support_detail_screen.dart';
import '../screens/support/support_list_screen.dart';

// Shell
import '../widgets/common/app_shell.dart';

/// Navigation shell key for bottom navigation
final _rootNavigatorKey = GlobalKey<NavigatorState>();

/// Auth routes that don't require authentication
const _publicRoutes = [
  AppRoutes.splash,
  AppRoutes.login,
  AppRoutes.magicLinkEmail,
  AppRoutes.magicLinkCode,
];

/// Routes that require authentication but not org selection
// Reachable with a session but no org: the picker, and the screen that
// creates the org the picker has none of.
const _authOnlyRoutes = [AppRoutes.orgSelection, AppRoutes.orgCreate];

/// Router Provider
final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: AppRoutes.splash,
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final authState = ref.read(authProvider);
      final isAuthenticated = authState.isAuthenticated;
      final needsOrgSelection = authState.needsOrgSelection;
      final currentPath = state.matchedLocation;

      // Allow public routes
      if (_publicRoutes.contains(currentPath)) {
        return null;
      }

      // Redirect to login if not authenticated
      if (!isAuthenticated) {
        return AppRoutes.login;
      }

      // Handle org selection routes
      if (_authOnlyRoutes.contains(currentPath)) {
        // Already on org selection, allow it
        return null;
      }

      // Redirect to org selection if needed
      if (needsOrgSelection) {
        return AppRoutes.orgSelection;
      }

      return null;
    },
    routes: [
      // ============================================
      // AUTH ROUTES (No bottom navigation)
      // ============================================
      GoRoute(
        path: AppRoutes.splash,
        name: 'splash',
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const SplashScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
        ),
      ),
      GoRoute(
        path: AppRoutes.login,
        name: 'login',
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const LoginScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
        ),
      ),
      GoRoute(
        path: AppRoutes.magicLinkEmail,
        name: 'magicLinkEmail',
        builder: (context, state) => const MagicLinkEmailScreen(),
      ),
      GoRoute(
        path: AppRoutes.magicLinkCode,
        name: 'magicLinkCode',
        builder: (context, state) {
          final email = state.uri.queryParameters['email'] ?? '';
          return MagicLinkCodeScreen(email: email);
        },
      ),
      GoRoute(
        path: AppRoutes.solutions,
        name: 'solutions',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.solutions,
          child: const SolutionsListScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.solutionNew,
        name: 'solutionNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.solutionNew,
          child: const SolutionDetailScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.solutionDetail,
        name: 'solutionDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final id = state.pathParameters['id']!;
          return ModuleGate(
            path: AppRoutes.solutionDetail,
            child: SolutionDetailScreen(solutionId: id),
          );
        },
      ),
      GoRoute(
        path: AppRoutes.accounts,
        name: 'accounts',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const AccountsListScreen(),
      ),
      GoRoute(
        path: AppRoutes.accountCreate,
        name: 'accountCreate',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const AccountFormScreen(),
      ),
      GoRoute(
        path: AppRoutes.accountEdit,
        name: 'accountEdit',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            AccountFormScreen(accountId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: AppRoutes.accountStatement,
        name: 'accountStatement',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.accountStatement,
          child: AccountStatementScreen(accountId: state.pathParameters['id']!),
        ),
      ),
      // Registered after `create` and `:id/edit` so those literal segments are
      // not swallowed by the `:id` parameter.
      GoRoute(
        path: AppRoutes.accountDetail,
        name: 'accountDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            AccountDetailScreen(accountId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: AppRoutes.contacts,
        name: 'contacts',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ContactsListScreen(),
      ),
      GoRoute(
        path: AppRoutes.contactCreate,
        name: 'contactCreate',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ContactFormScreen(),
      ),
      GoRoute(
        path: AppRoutes.contactEdit,
        name: 'contactEdit',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            ContactFormScreen(contactId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: AppRoutes.contactDetail,
        name: 'contactDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            ContactDetailScreen(contactId: state.pathParameters['id']!),
      ),
      GoRoute(
        path: AppRoutes.mergeCompare,
        name: 'mergeCompare',
        parentNavigatorKey: _rootNavigatorKey,
        // Only the three modules that merge, and only with a second record.
        redirect: (context, state) =>
            DuplicateModule.parse(state.pathParameters['module']) == null ||
                (state.uri.queryParameters['with'] ?? '').isEmpty
            ? AppRoutes.dashboard
            : null,
        builder: (context, state) {
          final module = DuplicateModule.parse(state.pathParameters['module'])!;
          final screen = MergeCompareScreen(
            module: module,
            recordId: state.pathParameters['id']!,
            otherId: state.uri.queryParameters['with']!,
          );
          return module == DuplicateModule.leads
              ? ModuleGate(path: AppRoutes.leads, child: screen)
              : screen;
        },
      ),
      GoRoute(
        path: AppRoutes.approvalsInbox,
        name: 'approvalsInbox',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.approvalsInbox,
          child: const ApprovalsInboxScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.ticketAnalytics,
        name: 'ticketAnalytics',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.ticketAnalytics,
          child: const TicketAnalyticsScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.ticketBoard,
        name: 'ticketBoard',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.ticketBoard,
          child: const TicketBoardScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.timesheet,
        name: 'timesheet',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.timesheet,
          child: const TimesheetScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.timeReport,
        name: 'timeReport',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.timeReport,
          child: const TimeReportScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.notifications,
        name: 'notifications',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const NotificationsScreen(),
      ),
      GoRoute(
        path: AppRoutes.documents,
        name: 'documents',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.documents,
          child: const DocumentsListScreen(),
        ),
      ),
      // Literal `new` before the `:id` pattern, or `/documents/new` is read as
      // a document whose id is the word "new".
      GoRoute(
        path: AppRoutes.documentNew,
        name: 'documentNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.documentNew,
          child: const DocumentFormScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.documentEdit,
        name: 'documentEdit',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.documentEdit,
          child: DocumentFormScreen(
            documentId: state.pathParameters['id'] ?? '',
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.goals,
        name: 'goals',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            ModuleGate(path: AppRoutes.goals, child: const GoalsScreen()),
      ),
      GoRoute(
        path: AppRoutes.goalNew,
        name: 'goalNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            ModuleGate(path: AppRoutes.goalNew, child: const GoalFormScreen()),
      ),
      GoRoute(
        path: AppRoutes.goalHistory,
        name: 'goalHistory',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.goalHistory,
          child: const GoalHistoryScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.goalEdit,
        name: 'goalEdit',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.goalEdit,
          child: GoalFormScreen(goalId: state.pathParameters['id'] ?? ''),
        ),
      ),
      GoRoute(
        path: AppRoutes.help,
        name: 'help',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SupportListScreen(),
      ),
      // Literal `new` must be declared before `:id`.
      GoRoute(
        path: AppRoutes.helpNew,
        name: 'helpNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SupportCreateScreen(),
      ),
      GoRoute(
        path: AppRoutes.helpDetail,
        name: 'helpDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            SupportDetailScreen(ticketId: state.pathParameters['id'] ?? ''),
      ),
      GoRoute(
        path: AppRoutes.invoices,
        name: 'invoices',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.invoices,
          child: const InvoicesListScreen(),
        ),
      ),
      // These five must stay above `invoiceDetail`. go_router matches in
      // declaration order, so `/invoices/:id` placed first would treat
      // "estimates" as an invoice id and every sibling page would 404 through
      // the detail screen instead of opening.
      GoRoute(
        path: AppRoutes.invoiceNew,
        name: 'invoiceNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.invoiceNew,
          child: const NewInvoiceScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.recurringNew,
        name: 'recurringNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.recurringNew,
          child: const NewRecurringScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.estimates,
        name: 'estimates',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.estimates,
          child: const EstimatesListScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.estimateNew,
        name: 'estimateNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.estimateNew,
          child: NewEstimateScreen(
            fromDeal: state.extra is Deal ? state.extra as Deal : null,
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.recurring,
        name: 'recurring',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.recurring,
          child: const RecurringListScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.products,
        name: 'products',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.products,
          child: const ProductsListScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.invoiceTemplates,
        name: 'invoiceTemplates',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.invoiceTemplates,
          child: const InvoiceTemplatesScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.invoiceTemplateNew,
        name: 'invoiceTemplateNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.invoiceTemplateNew,
          child: const InvoiceTemplateFormScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.invoiceTemplateEdit,
        name: 'invoiceTemplateEdit',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.invoiceTemplateEdit,
          child: InvoiceTemplateFormScreen(
            templateId: state.pathParameters['id'],
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.invoiceReports,
        name: 'invoiceReports',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.invoiceReports,
          child: const InvoiceReportsScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.invoiceDetail,
        name: 'invoiceDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.invoiceDetail,
          child: InvoiceDetailScreen(
            invoiceId: state.pathParameters['id'] ?? '',
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.profile,
        name: 'profile',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: AppRoutes.team,
        name: 'team',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const TeamScreen(),
      ),
      GoRoute(
        path: AppRoutes.settings,
        name: 'settings',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SettingsHubScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsCustomFields,
        name: 'settingsCustomFields',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const CustomFieldsScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsMacros,
        name: 'settingsMacros',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsMacros,
          child: const MacrosScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsTags,
        name: 'settingsTags',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const TagsScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsLeadPipelines,
        name: 'settingsLeadPipelines',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsLeadPipelines,
          child: const LeadPipelinesScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsLeadPipelineDetail,
        name: 'settingsLeadPipelineDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsLeadPipelineDetail,
          child: LeadPipelineDetailScreen(
            pipelineId: state.pathParameters['pipelineId'] ?? '',
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsDealPipelines,
        name: 'settingsDealPipelines',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsDealPipelines,
          child: const DealPipelinesScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsDealPipelineDetail,
        name: 'settingsDealPipelineDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsDealPipelineDetail,
          child: DealPipelineDetailScreen(
            pipelineId: state.pathParameters['pipelineId'] ?? '',
          ),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsWebForms,
        name: 'settingsWebForms',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const WebFormsScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsWebFormDetail,
        name: 'settingsWebFormDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) =>
            WebFormDetailScreen(formId: state.pathParameters['formId'] ?? ''),
      ),
      GoRoute(
        path: AppRoutes.settingsWebhooks,
        name: 'settingsWebhooks',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const WebhooksScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsWebhookDetail,
        name: 'settingsWebhookDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => WebhookDetailScreen(
          webhookId: state.pathParameters['webhookId'] ?? '',
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsAutomation,
        name: 'settingsAutomation',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const AutomationRulesScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsAutomationNew,
        name: 'settingsAutomationNew',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const AutomationRuleScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsAutomationRuleDetail,
        name: 'settingsAutomationRuleDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => AutomationRuleScreen(
          key: ValueKey('automation-rule-${state.pathParameters['ruleId']}'),
          ruleId: state.pathParameters['ruleId'] ?? '',
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsAutomationRunsDetail,
        name: 'settingsAutomationRunsDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => AutomationRunsScreen(
          key: ValueKey('automation-runs-${state.pathParameters['ruleId']}'),
          ruleId: state.pathParameters['ruleId'] ?? '',
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsAuditLog,
        name: 'settingsAuditLog',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const AuditLogScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsRouting,
        name: 'settingsRouting',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsRouting,
          child: const RoutingScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsEscalation,
        name: 'settingsEscalation',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsEscalation,
          child: const EscalationScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsBusinessHours,
        name: 'settingsBusinessHours',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsBusinessHours,
          child: const BusinessHoursScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsReopen,
        name: 'settingsReopen',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsReopen,
          child: const ReopenScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.objectRecordsPattern,
        name: 'objectRecords',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final key = state.pathParameters['key'] ?? '';
          return ObjectRecordsScreen(
            key: ValueKey('objects-$key'),
            objectKey: key,
          );
        },
      ),
      GoRoute(
        path: AppRoutes.objectRecordCreatePattern,
        name: 'objectRecordCreate',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ObjectRecordFormScreen(
          key: ValueKey('object-new-${state.pathParameters['key']}'),
          objectKey: state.pathParameters['key'] ?? '',
        ),
      ),
      GoRoute(
        path: AppRoutes.objectRecordPattern,
        name: 'objectRecord',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ObjectRecordDetailScreen(
          key: ValueKey('object-record-${state.pathParameters['id']}'),
          objectKey: state.pathParameters['key'] ?? '',
          recordId: state.pathParameters['id'] ?? '',
        ),
      ),
      GoRoute(
        path: AppRoutes.objectRecordEditPattern,
        name: 'objectRecordEdit',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ObjectRecordFormScreen(
          key: ValueKey('object-edit-${state.pathParameters['id']}'),
          objectKey: state.pathParameters['key'] ?? '',
          recordId: state.pathParameters['id'],
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsObjects,
        name: 'settingsObjects',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ObjectsSettingsScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsObjectPattern,
        name: 'settingsObject',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ObjectSettingsScreen(
          key: ValueKey('object-settings-${state.pathParameters['key']}'),
          objectKey: state.pathParameters['key'] ?? '',
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsHelpCenter,
        name: 'settingsHelpCenter',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsHelpCenter,
          child: const HelpCenterScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsInboundEmail,
        name: 'settingsInboundEmail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsInboundEmail,
          child: const InboundEmailScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsTicketApprovals,
        name: 'settingsTicketApprovals',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.settingsTicketApprovals,
          child: const ApprovalRulesScreen(),
        ),
      ),
      GoRoute(
        path: AppRoutes.settingsApiTokens,
        name: 'settingsApiTokens',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ApiTokensScreen(),
      ),
      GoRoute(
        path: AppRoutes.profileTokens,
        name: 'profileTokens',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const MyApiTokensScreen(),
      ),
      GoRoute(
        path: AppRoutes.profileCalendarFeed,
        name: 'profileCalendarFeed',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ModuleGate(
          path: AppRoutes.profileCalendarFeed,
          child: const CalendarFeedScreen(),
        ),
      ),
      // The edit route is declared before the read one so `/organization/edit`
      // is never captured as a sub-path of `/organization`.
      GoRoute(
        path: AppRoutes.settingsOrganizationEdit,
        name: 'settingsOrganizationEdit',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const OrganizationEditScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsModules,
        name: 'settingsModules',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ModulesScreen(),
      ),
      GoRoute(
        path: AppRoutes.settingsOrganization,
        name: 'settingsOrganization',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const OrganizationScreen(),
      ),
      GoRoute(
        path: AppRoutes.orgCreate,
        name: 'orgCreate',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const OrgCreateScreen(),
      ),
      GoRoute(
        path: AppRoutes.importWelcome,
        name: 'importWelcome',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ImportWelcomeScreen(),
      ),
      GoRoute(
        path: AppRoutes.orgSelection,
        name: 'orgSelection',
        pageBuilder: (context, state) => CustomTransitionPage(
          key: state.pageKey,
          child: const OrgSelectionScreen(),
          transitionsBuilder: (context, animation, secondaryAnimation, child) {
            return FadeTransition(opacity: animation, child: child);
          },
        ),
      ),

      // ============================================
      // MAIN APP ROUTES (With bottom navigation)
      // ============================================
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return AppShell(navigationShell: navigationShell);
        },
        branches: [
          // Dashboard Branch
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.dashboard,
                name: 'dashboard',
                builder: (context, state) => const DashboardScreen(),
              ),
            ],
          ),

          // Leads Branch
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.leads,
                name: 'leads',
                // Keyed on `view` so arriving from a dashboard badge builds a
                // fresh State. Without the key Flutter reuses the one already
                // in this shell branch, whose initState has long since run,
                // and the list opens unfiltered.
                builder: (context, state) {
                  final view = state.uri.queryParameters['view'];
                  return ModuleGate(
                    path: AppRoutes.leads,
                    child: LeadsListScreen(
                      key: ValueKey('leads-$view'),
                      initialView: view,
                    ),
                  );
                },
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'leadCreate',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => const ModuleGate(
                      path: AppRoutes.leadCreate,
                      child: LeadCreateScreen(),
                    ),
                  ),
                  // Before `:id`, which would otherwise swallow "board" and
                  // ask the leads API for a lead with that id.
                  GoRoute(
                    path: 'board',
                    name: 'leadBoard',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => const ModuleGate(
                      path: AppRoutes.leadBoard,
                      child: LeadBoardScreen(),
                    ),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'leadDetail',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return ModuleGate(
                        path: AppRoutes.leadDetail,
                        child: LeadDetailScreen(leadId: id),
                      );
                    },
                    routes: [
                      GoRoute(
                        path: 'edit',
                        name: 'leadEdit',
                        parentNavigatorKey: _rootNavigatorKey,
                        builder: (context, state) {
                          final id = state.pathParameters['id']!;
                          return ModuleGate(
                            path: AppRoutes.leadEdit,
                            child: LeadFormScreen(leadId: id),
                          );
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),

          // Deals Branch
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.deals,
                name: 'deals',
                builder: (context, state) => const ModuleGate(
                  path: AppRoutes.deals,
                  child: DealsListScreen(),
                ),
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'dealCreate',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => ModuleGate(
                      path: AppRoutes.dealCreate,
                      child: DealFormScreen(
                        accountId: state.uri.queryParameters['accountId'],
                      ),
                    ),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'dealDetail',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return ModuleGate(
                        path: AppRoutes.dealDetail,
                        child: DealDetailScreen(dealId: id),
                      );
                    },
                    routes: [
                      GoRoute(
                        path: 'edit',
                        name: 'dealEdit',
                        parentNavigatorKey: _rootNavigatorKey,
                        builder: (context, state) {
                          final id = state.pathParameters['id']!;
                          return ModuleGate(
                            path: '/deals/:id/edit',
                            child: DealFormScreen(dealId: id),
                          );
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),

          // Tickets Branch
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.tickets,
                name: 'tickets',
                builder: (context, state) => const ModuleGate(
                  path: AppRoutes.tickets,
                  child: TicketsListScreen(),
                ),
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'ticketCreate',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => const ModuleGate(
                      path: AppRoutes.ticketCreate,
                      child: TicketCreateScreen(),
                    ),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'ticketDetail',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return ModuleGate(
                        path: AppRoutes.ticketDetail,
                        child: TicketDetailScreen(ticketId: id),
                      );
                    },
                    routes: [
                      GoRoute(
                        path: 'edit',
                        name: 'ticketEdit',
                        parentNavigatorKey: _rootNavigatorKey,
                        builder: (context, state) {
                          final id = state.pathParameters['id']!;
                          return ModuleGate(
                            path: AppRoutes.ticketEdit,
                            child: TicketFormScreen(ticketId: id),
                          );
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),

          // Tasks Branch
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.tasks,
                name: 'tasks',
                // Keyed on `view` for the same reason as the leads branch.
                builder: (context, state) {
                  final view = state.uri.queryParameters['view'];
                  return ModuleGate(
                    path: AppRoutes.tasks,
                    child: TasksListScreen(
                      key: ValueKey('tasks-$view'),
                      initialView: view,
                    ),
                  );
                },
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'taskCreate',
                    parentNavigatorKey: _rootNavigatorKey,
                    // `?due=YYYY-MM-DD` carries the day the user tapped in the
                    // calendar, which the form used to discard.
                    builder: (context, state) => ModuleGate(
                      path: AppRoutes.taskCreate,
                      child: TaskFormScreen(
                        initialDueDate: DateTime.tryParse(
                          state.uri.queryParameters['due'] ?? '',
                        ),
                      ),
                    ),
                  ),
                  // Before `:id`, which would otherwise swallow "board" and
                  // ask the tasks API for a task with that id.
                  GoRoute(
                    path: 'board',
                    name: 'taskBoard',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => const ModuleGate(
                      path: AppRoutes.taskBoard,
                      child: BoardScreen(),
                    ),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'taskDetail',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return ModuleGate(
                        path: AppRoutes.taskDetail,
                        child: TaskDetailScreen(taskId: id),
                      );
                    },
                    routes: [
                      GoRoute(
                        path: 'edit',
                        name: 'taskEdit',
                        parentNavigatorKey: _rootNavigatorKey,
                        builder: (context, state) {
                          final id = state.pathParameters['id']!;
                          return ModuleGate(
                            path: AppRoutes.taskEdit,
                            child: TaskFormScreen(taskId: id),
                          );
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),

          // More/Settings Branch
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: AppRoutes.more,
                name: 'more',
                builder: (context, state) => const MoreScreen(),
              ),
            ],
          ),
        ],
      ),
    ],

    // Error page
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(LucideIcons.circleAlert, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(
              'Page not found',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              state.uri.toString(),
              style: Theme.of(
                context,
              ).textTheme.bodyMedium?.copyWith(color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go(AppRoutes.dashboard),
              child: const Text('Go to Dashboard'),
            ),
          ],
        ),
      ),
    ),
  );
});
