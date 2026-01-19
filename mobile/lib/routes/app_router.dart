import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';

// Auth Screens
import '../screens/auth/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/auth/org_selection_screen.dart';

// Main Screens
import '../screens/dashboard/dashboard_screen.dart';
import '../screens/leads/leads_list_screen.dart';
import '../screens/leads/lead_detail_screen.dart';
import '../screens/leads/lead_create_screen.dart';
import '../screens/leads/lead_form_screen.dart';
import '../screens/deals/deals_list_screen.dart';
import '../screens/deals/deal_detail_screen.dart';
import '../screens/deals/deal_form_screen.dart';
import '../screens/tasks/tasks_list_screen.dart';
import '../screens/tasks/task_detail_screen.dart';
import '../screens/tasks/task_form_screen.dart';
import '../screens/settings/more_screen.dart';

// Shell
import '../widgets/common/app_shell.dart';

/// App Routes
class AppRoutes {
  AppRoutes._();

  // Auth routes
  static const String splash = '/splash';
  static const String login = '/login';
  static const String forgotPassword = '/forgot-password';
  static const String orgSelection = '/org-selection';

  // Main routes
  static const String dashboard = '/dashboard';
  static const String leads = '/leads';
  static const String leadDetail = '/leads/:id';
  static const String leadCreate = '/leads/create';
  static const String leadEdit = '/leads/:id/edit';
  static const String deals = '/deals';
  static const String dealDetail = '/deals/:id';
  static const String dealCreate = '/deals/create';
  static const String tasks = '/tasks';
  static const String taskDetail = '/tasks/:id';
  static const String taskCreate = '/tasks/create';
  static const String taskEdit = '/tasks/:id/edit';
  static const String more = '/more';
  static const String profile = '/more/profile';
  static const String notifications = '/more/notifications';
  static const String team = '/more/team';
}

/// Navigation shell key for bottom navigation
final _rootNavigatorKey = GlobalKey<NavigatorState>();

/// Auth routes that don't require authentication
const _publicRoutes = [
  AppRoutes.splash,
  AppRoutes.login,
  AppRoutes.forgotPassword,
];

/// Routes that require authentication but not org selection
const _authOnlyRoutes = [
  AppRoutes.orgSelection,
];

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
        path: AppRoutes.forgotPassword,
        name: 'forgotPassword',
        builder: (context, state) => const ForgotPasswordScreen(),
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
                builder: (context, state) => const LeadsListScreen(),
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'leadCreate',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => const LeadCreateScreen(),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'leadDetail',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return LeadDetailScreen(leadId: id);
                    },
                    routes: [
                      GoRoute(
                        path: 'edit',
                        name: 'leadEdit',
                        parentNavigatorKey: _rootNavigatorKey,
                        builder: (context, state) {
                          final id = state.pathParameters['id']!;
                          return LeadFormScreen(leadId: id);
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
                builder: (context, state) => const DealsListScreen(),
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'dealCreate',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => const DealFormScreen(),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'dealDetail',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return DealDetailScreen(dealId: id);
                    },
                    routes: [
                      GoRoute(
                        path: 'edit',
                        name: 'dealEdit',
                        parentNavigatorKey: _rootNavigatorKey,
                        builder: (context, state) {
                          final id = state.pathParameters['id']!;
                          return DealFormScreen(dealId: id);
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
                builder: (context, state) => const TasksListScreen(),
                routes: [
                  GoRoute(
                    path: 'create',
                    name: 'taskCreate',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) => const TaskFormScreen(),
                  ),
                  GoRoute(
                    path: ':id',
                    name: 'taskDetail',
                    parentNavigatorKey: _rootNavigatorKey,
                    builder: (context, state) {
                      final id = state.pathParameters['id']!;
                      return TaskDetailScreen(taskId: id);
                    },
                    routes: [
                      GoRoute(
                        path: 'edit',
                        name: 'taskEdit',
                        parentNavigatorKey: _rootNavigatorKey,
                        builder: (context, state) {
                          final id = state.pathParameters['id']!;
                          return TaskFormScreen(taskId: id);
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
            const Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.grey,
            ),
            const SizedBox(height: 16),
            Text(
              'Page not found',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              state.uri.toString(),
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey,
                  ),
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
