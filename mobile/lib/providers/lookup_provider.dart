import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/lookup_models.dart';
import '../services/api_service.dart';

/// Lookup providers — one AsyncNotifier per resource so the four fetches
/// (accounts / contacts / users / tags) cache, refresh and surface
/// loading/error independently.
///
/// Forms watch the convenience `Provider<List<X>>` wrappers below for the
/// resolved list, and read the underlying `AsyncNotifierProvider`s directly
/// when they need the loading flag.

final ApiService _apiService = ApiService();

/// Accounts
class AccountsLookupNotifier extends AsyncNotifier<List<AccountLookup>> {
  @override
  Future<List<AccountLookup>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<List<AccountLookup>> _fetch() async {
    final response = await _apiService.get(ApiConfig.accounts);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load accounts');
    }
    final data = response.data!;
    List<dynamic> list = [];
    if (data['accounts'] != null) {
      list = data['accounts'] as List<dynamic>? ?? [];
    } else if (data['results'] != null) {
      list = data['results'] as List<dynamic>? ?? [];
    }
    return list
        .whereType<Map<String, dynamic>>()
        .map(AccountLookup.fromJson)
        .toList();
  }
}

final accountsLookupProvider =
    AsyncNotifierProvider<AccountsLookupNotifier, List<AccountLookup>>(
      AccountsLookupNotifier.new,
    );

/// Contacts
class ContactsLookupNotifier extends AsyncNotifier<List<ContactLookup>> {
  @override
  Future<List<ContactLookup>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<List<ContactLookup>> _fetch() async {
    final response = await _apiService.get(ApiConfig.contacts);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load contacts');
    }
    final data = response.data!;
    List<dynamic> list = [];
    if (data['contacts'] != null) {
      list = data['contacts'] as List<dynamic>? ?? [];
    } else if (data['results'] != null) {
      list = data['results'] as List<dynamic>? ?? [];
    }
    return list
        .whereType<Map<String, dynamic>>()
        .map(ContactLookup.fromJson)
        .toList();
  }
}

final contactsLookupProvider =
    AsyncNotifierProvider<ContactsLookupNotifier, List<ContactLookup>>(
      ContactsLookupNotifier.new,
    );

/// Users (active profiles)
class UsersLookupNotifier extends AsyncNotifier<List<UserLookup>> {
  @override
  Future<List<UserLookup>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<List<UserLookup>> _fetch() async {
    final response = await _apiService.get(ApiConfig.teamsAndUsers);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load users');
    }
    final profiles = response.data!['profiles'] as List<dynamic>? ?? [];
    return profiles
        .whereType<Map<String, dynamic>>()
        .map(UserLookup.fromJson)
        .where((u) => u.isActive)
        .toList();
  }
}

final usersLookupProvider =
    AsyncNotifierProvider<UsersLookupNotifier, List<UserLookup>>(
      UsersLookupNotifier.new,
    );

/// Tags
class TagsLookupNotifier extends AsyncNotifier<List<TagLookup>> {
  @override
  Future<List<TagLookup>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<List<TagLookup>> _fetch() async {
    final response = await _apiService.get(ApiConfig.tags);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load tags');
    }
    final data = response.data!;
    List<dynamic> list = [];
    if (data['tags'] != null) {
      list = data['tags'] as List<dynamic>? ?? [];
    } else if (data['results'] != null) {
      list = data['results'] as List<dynamic>? ?? [];
    }
    return list
        .whereType<Map<String, dynamic>>()
        .map(TagLookup.fromJson)
        .toList();
  }
}

final tagsLookupProvider =
    AsyncNotifierProvider<TagsLookupNotifier, List<TagLookup>>(
      TagsLookupNotifier.new,
    );

/// Convenience wrappers — return the resolved list (or empty during
/// load/error). Forms that don't care about loading state watch these.
final accountsProvider = Provider<List<AccountLookup>>((ref) {
  return ref.watch(accountsLookupProvider).value ?? const [];
});

final contactsProvider = Provider<List<ContactLookup>>((ref) {
  return ref.watch(contactsLookupProvider).value ?? const [];
});

final usersProvider = Provider<List<UserLookup>>((ref) {
  return ref.watch(usersLookupProvider).value ?? const [];
});

final tagsProvider = Provider<List<TagLookup>>((ref) {
  return ref.watch(tagsLookupProvider).value ?? const [];
});
