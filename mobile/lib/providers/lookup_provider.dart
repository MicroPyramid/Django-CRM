import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/lookup_models.dart';
import '../services/api_service.dart';

/// State for lookup data (accounts, contacts, users, tags)
class LookupState {
  final List<AccountLookup> accounts;
  final List<ContactLookup> contacts;
  final List<UserLookup> users;
  final List<TagLookup> tags;
  final bool isLoadingAccounts;
  final bool isLoadingContacts;
  final bool isLoadingUsers;
  final bool isLoadingTags;
  final String? error;

  const LookupState({
    this.accounts = const [],
    this.contacts = const [],
    this.users = const [],
    this.tags = const [],
    this.isLoadingAccounts = false,
    this.isLoadingContacts = false,
    this.isLoadingUsers = false,
    this.isLoadingTags = false,
    this.error,
  });

  const LookupState.initial()
      : accounts = const [],
        contacts = const [],
        users = const [],
        tags = const [],
        isLoadingAccounts = false,
        isLoadingContacts = false,
        isLoadingUsers = false,
        isLoadingTags = false,
        error = null;

  bool get isLoading =>
      isLoadingAccounts || isLoadingContacts || isLoadingUsers || isLoadingTags;

  LookupState copyWith({
    List<AccountLookup>? accounts,
    List<ContactLookup>? contacts,
    List<UserLookup>? users,
    List<TagLookup>? tags,
    bool? isLoadingAccounts,
    bool? isLoadingContacts,
    bool? isLoadingUsers,
    bool? isLoadingTags,
    String? error,
    bool clearError = false,
  }) {
    return LookupState(
      accounts: accounts ?? this.accounts,
      contacts: contacts ?? this.contacts,
      users: users ?? this.users,
      tags: tags ?? this.tags,
      isLoadingAccounts: isLoadingAccounts ?? this.isLoadingAccounts,
      isLoadingContacts: isLoadingContacts ?? this.isLoadingContacts,
      isLoadingUsers: isLoadingUsers ?? this.isLoadingUsers,
      isLoadingTags: isLoadingTags ?? this.isLoadingTags,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

/// Notifier for managing lookup data
class LookupNotifier extends StateNotifier<LookupState> {
  LookupNotifier() : super(const LookupState.initial());

  final ApiService _apiService = ApiService();

  /// Fetch all lookup data
  Future<void> fetchAll() async {
    await Future.wait([
      fetchAccounts(),
      fetchContacts(),
      fetchUsers(),
      fetchTags(),
    ]);
  }

  /// Fetch accounts
  Future<void> fetchAccounts() async {
    if (state.isLoadingAccounts) return;

    state = state.copyWith(isLoadingAccounts: true, clearError: true);

    try {
      final response = await _apiService.get(ApiConfig.accounts);

      if (response.success && response.data != null) {
        final data = response.data!;

        // Parse accounts - handle different response formats
        List<dynamic> accountsList = [];
        if (data['accounts'] != null) {
          accountsList = data['accounts'] as List<dynamic>? ?? [];
        } else if (data['results'] != null) {
          accountsList = data['results'] as List<dynamic>? ?? [];
        }

        final accounts = <AccountLookup>[];
        for (final item in accountsList) {
          if (item is Map<String, dynamic>) {
            accounts.add(AccountLookup.fromJson(item));
          }
        }

        state = state.copyWith(
          accounts: accounts,
          isLoadingAccounts: false,
        );
      } else {
        state = state.copyWith(
          isLoadingAccounts: false,
          error: response.message ?? 'Failed to load accounts',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoadingAccounts: false,
        error: 'Failed to load accounts: ${e.toString()}',
      );
    }
  }

  /// Fetch contacts
  Future<void> fetchContacts() async {
    if (state.isLoadingContacts) return;

    state = state.copyWith(isLoadingContacts: true, clearError: true);

    try {
      final response = await _apiService.get(ApiConfig.contacts);

      if (response.success && response.data != null) {
        final data = response.data!;

        // Parse contacts - handle different response formats
        List<dynamic> contactsList = [];
        if (data['contacts'] != null) {
          contactsList = data['contacts'] as List<dynamic>? ?? [];
        } else if (data['results'] != null) {
          contactsList = data['results'] as List<dynamic>? ?? [];
        }

        final contacts = <ContactLookup>[];
        for (final item in contactsList) {
          if (item is Map<String, dynamic>) {
            contacts.add(ContactLookup.fromJson(item));
          }
        }

        state = state.copyWith(
          contacts: contacts,
          isLoadingContacts: false,
        );
      } else {
        state = state.copyWith(
          isLoadingContacts: false,
          error: response.message ?? 'Failed to load contacts',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoadingContacts: false,
        error: 'Failed to load contacts: ${e.toString()}',
      );
    }
  }

  /// Fetch users (profiles for assignment)
  Future<void> fetchUsers() async {
    if (state.isLoadingUsers) return;

    state = state.copyWith(isLoadingUsers: true, clearError: true);

    try {
      final response = await _apiService.get(ApiConfig.teamsAndUsers);

      if (response.success && response.data != null) {
        final data = response.data!;

        // Parse profiles from the response
        List<dynamic> profilesList = [];
        if (data['profiles'] != null) {
          profilesList = data['profiles'] as List<dynamic>? ?? [];
        }

        final users = <UserLookup>[];
        for (final item in profilesList) {
          if (item is Map<String, dynamic>) {
            final user = UserLookup.fromJson(item);
            // Only include active users
            if (user.isActive) {
              users.add(user);
            }
          }
        }

        state = state.copyWith(
          users: users,
          isLoadingUsers: false,
        );
      } else {
        state = state.copyWith(
          isLoadingUsers: false,
          error: response.message ?? 'Failed to load users',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoadingUsers: false,
        error: 'Failed to load users: ${e.toString()}',
      );
    }
  }

  /// Fetch tags
  Future<void> fetchTags() async {
    if (state.isLoadingTags) return;

    state = state.copyWith(isLoadingTags: true, clearError: true);

    try {
      final response = await _apiService.get(ApiConfig.tags);

      if (response.success && response.data != null) {
        final data = response.data!;

        // Parse tags from the response
        List<dynamic> tagsList = [];
        if (data['tags'] != null) {
          tagsList = data['tags'] as List<dynamic>? ?? [];
        } else if (data['results'] != null) {
          tagsList = data['results'] as List<dynamic>? ?? [];
        }

        final tags = <TagLookup>[];
        for (final item in tagsList) {
          if (item is Map<String, dynamic>) {
            tags.add(TagLookup.fromJson(item));
          }
        }

        state = state.copyWith(
          tags: tags,
          isLoadingTags: false,
        );
      } else {
        state = state.copyWith(
          isLoadingTags: false,
          error: response.message ?? 'Failed to load tags',
        );
      }
    } catch (e) {
      state = state.copyWith(
        isLoadingTags: false,
        error: 'Failed to load tags: ${e.toString()}',
      );
    }
  }

  /// Get account by ID
  AccountLookup? getAccountById(String? id) {
    if (id == null || id.isEmpty) return null;
    try {
      return state.accounts.firstWhere((a) => a.id == id);
    } catch (_) {
      return null;
    }
  }

  /// Get contact by ID
  ContactLookup? getContactById(String? id) {
    if (id == null || id.isEmpty) return null;
    try {
      return state.contacts.firstWhere((c) => c.id == id);
    } catch (_) {
      return null;
    }
  }

  /// Get user by ID
  UserLookup? getUserById(String? id) {
    if (id == null || id.isEmpty) return null;
    try {
      return state.users.firstWhere((u) => u.id == id);
    } catch (_) {
      return null;
    }
  }

  /// Get tag by ID
  TagLookup? getTagById(String? id) {
    if (id == null || id.isEmpty) return null;
    try {
      return state.tags.firstWhere((t) => t.id == id);
    } catch (_) {
      return null;
    }
  }

  /// Get contacts by IDs
  List<ContactLookup> getContactsByIds(List<String> ids) {
    return state.contacts.where((c) => ids.contains(c.id)).toList();
  }

  /// Get users by IDs
  List<UserLookup> getUsersByIds(List<String> ids) {
    return state.users.where((u) => ids.contains(u.id)).toList();
  }

  /// Get tags by IDs
  List<TagLookup> getTagsByIds(List<String> ids) {
    return state.tags.where((t) => ids.contains(t.id)).toList();
  }

  /// Clear all data
  void clear() {
    state = const LookupState.initial();
  }
}

/// Main lookup provider
final lookupProvider = StateNotifierProvider<LookupNotifier, LookupState>((ref) {
  return LookupNotifier();
});

/// Convenience providers
final accountsProvider = Provider<List<AccountLookup>>((ref) {
  return ref.watch(lookupProvider).accounts;
});

final contactsProvider = Provider<List<ContactLookup>>((ref) {
  return ref.watch(lookupProvider).contacts;
});

final usersProvider = Provider<List<UserLookup>>((ref) {
  return ref.watch(lookupProvider).users;
});

final tagsProvider = Provider<List<TagLookup>>((ref) {
  return ref.watch(lookupProvider).tags;
});

final lookupLoadingProvider = Provider<bool>((ref) {
  return ref.watch(lookupProvider).isLoading;
});
