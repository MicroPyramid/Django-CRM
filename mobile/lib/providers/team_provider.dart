import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config/api_config.dart';
import '../data/models/team_member.dart';
import '../services/api_service.dart';

export '../services/api_service.dart' show ApiResponse;

/// Everyone in the org, split the way `/api/users/` splits them.
///
/// `forbidden` is a fact rather than an error. `/api/users/` is admin-only and
/// answers 403 to a member, and this screen is reachable from More by anyone,
/// so the 403 has to render as "admins only" instead of a failed load. The
/// distinction matters: an error state offers Retry, which would fail forever.
class TeamListData {
  const TeamListData({
    this.active = const [],
    this.inactive = const [],
    this.forbidden = false,
  });

  final List<TeamMember> active;
  final List<TeamMember> inactive;
  final bool forbidden;

  int get adminCount => active.where((m) => m.isAdmin).length;
  int get neverSignedInCount => active.where((m) => m.hasNeverSignedIn).length;

  /// Tokens still authenticating as someone whose login has been pulled.
  int get tokensOnDeactivated =>
      inactive.fold(0, (sum, m) => sum + m.activeTokenCount);

  /// The only admin left, if there is only one.
  ///
  /// The server refuses to demote or deactivate them; the screen hides those
  /// controls so the refusal is not the first the user hears of it. The hiding
  /// is a courtesy, the refusal is the rule.
  TeamMember? get lastAdmin {
    final admins = active.where((m) => m.isAdmin).toList();
    return admins.length == 1 ? admins.first : null;
  }
}

class TeamNotifier extends AsyncNotifier<TeamListData> {
  final ApiService _apiService = ApiService();

  @override
  Future<TeamListData> build() => _fetch();

  Future<TeamListData> _fetch() async {
    final response = await _apiService.get(ApiConfig.orgUsers);
    if (response.statusCode == 403) {
      return const TeamListData(forbidden: true);
    }
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Could not load the team.');
    }
    final data = response.data!;
    return TeamListData(
      active: _rows(data['active_users'], 'active_users'),
      inactive: _rows(data['inactive_users'], 'inactive_users'),
    );
  }

  /// The rows live one level down, under a key repeating the group's name
  /// (`active_users.active_users`). Reading the outer object as the list is
  /// what left the accounts screen empty for a week, so the path is explicit.
  List<TeamMember> _rows(dynamic group, String key) {
    if (group is! Map<String, dynamic>) return const [];
    final rows = group[key];
    if (rows is! List) return const [];
    return rows
        .whereType<Map<String, dynamic>>()
        .map(TeamMember.fromJson)
        .toList();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  /// Invite someone by email. The server picks up from here: it gates this to
  /// admins, refuses a duplicate inside the org, and reuses an account that
  /// already exists in another one.
  Future<ApiResponse<Map<String, dynamic>>> invite({
    required String email,
    required String role,
  }) async {
    final response = await _apiService.post(ApiConfig.orgUsers, {
      'email': email,
      'role': role,
    });
    if (response.success) await refresh();
    return response;
  }

  /// Change someone's role. `userId` is the User id; sending the profile id
  /// here addresses a different table and quietly does nothing useful.
  Future<ApiResponse<Map<String, dynamic>>> setRole({
    required String userId,
    required String role,
  }) async {
    final response = await _apiService.patch(ApiConfig.orgUser(userId), {
      'role': role,
    });
    if (response.success) await refresh();
    return response;
  }

  Future<ApiResponse<Map<String, dynamic>>> setActive({
    required String userId,
    required bool isActive,
  }) async {
    final response = await _apiService.post(ApiConfig.orgUserStatus(userId), {
      'status': isActive ? 'Active' : 'Inactive',
    });
    if (response.success) await refresh();
    return response;
  }
}

final teamProvider = AsyncNotifierProvider<TeamNotifier, TeamListData>(
  TeamNotifier.new,
);
