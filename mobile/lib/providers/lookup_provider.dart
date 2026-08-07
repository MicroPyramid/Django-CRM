import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/api_envelope.dart';
import '../data/models/lookup_models.dart';
import '../data/models/custom_field_definition.dart';
import '../services/api_service.dart';

/// Lookup providers, one AsyncNotifier per resource so the four fetches
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
    // `/api/accounts/` nests its rows under `active_accounts.open_accounts`
    // and publishes neither `accounts` nor `results`, which is why this picker
    // was permanently empty: both old guesses missed, and a miss reads as "no
    // accounts" rather than as an error. Inactive accounts sit under
    // `closed_accounts.close_accounts` and are deliberately not offered.
    return listFromEnvelope(response.data!, const [
      'active_accounts.open_accounts',
      'accounts',
      'results',
    ]).map(AccountLookup.fromJson).toList();
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
    return listFromEnvelope(response.data!, const [
      'results',
      'contacts',
    ]).map(ContactLookup.fromJson).toList();
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
    return listFromEnvelope(response.data!, const ['profiles'])
        .map(UserLookup.fromJson)
        .where((u) => u.isActive)
        .toList();
  }
}

final usersLookupProvider =
    AsyncNotifierProvider<UsersLookupNotifier, List<UserLookup>>(
      UsersLookupNotifier.new,
    );

/// Teams. Backed by the same teams_and_users endpoint as the users lookup, so
/// hitting it twice in one frame still only fires one network request (the
/// underlying ApiService doesn't dedupe. These notifiers each call it once and
/// cache).
class TeamsLookupNotifier extends AsyncNotifier<List<TeamLookup>> {
  @override
  Future<List<TeamLookup>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<List<TeamLookup>> _fetch() async {
    final response = await _apiService.get(ApiConfig.teamsAndUsers);
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load teams');
    }
    return listFromEnvelope(response.data!, const ['teams'])
        .map(TeamLookup.fromJson)
        .where((t) => t.id.isNotEmpty && t.name.isNotEmpty)
        .toList();
  }
}

final teamsLookupProvider =
    AsyncNotifierProvider<TeamsLookupNotifier, List<TeamLookup>>(
      TeamsLookupNotifier.new,
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
    return listFromEnvelope(response.data!, const [
      'tags',
      'results',
    ]).map(TagLookup.fromJson).toList();
  }
}

final tagsLookupProvider =
    AsyncNotifierProvider<TagsLookupNotifier, List<TagLookup>>(
      TagsLookupNotifier.new,
    );

/// Convenience wrappers. Return the resolved list (or empty during
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

final teamsProvider = Provider<List<TeamLookup>>((ref) {
  return ref.watch(teamsLookupProvider).value ?? const [];
});

/// Custom field definitions, keyed by target_model (Case, Lead, ...).
///
/// Each form watches the family for its entity; results are cached per-target
/// for the lifetime of the provider scope so reopening the same form is cheap.
final customFieldDefinitionsProvider =
    FutureProvider.family<List<CustomFieldDefinition>, String>((
      ref,
      targetModel,
    ) async {
      final url = Uri.parse(ApiConfig.customFieldDefinitions)
          .replace(
            queryParameters: {
              'target_model': targetModel,
              'active_only': 'true',
            },
          )
          .toString();
      final response = await _apiService.get(url);
      if (!response.success || response.data == null) {
        throw Exception(response.message ?? 'Failed to load custom fields');
      }
      final parsed = listFromEnvelope(response.data!, const ['definitions'])
          .map(CustomFieldDefinition.fromJson)
          .toList();
      parsed.sort((a, b) {
        final byOrder = a.displayOrder.compareTo(b.displayOrder);
        return byOrder != 0 ? byOrder : a.label.compareTo(b.label);
      });
      return parsed;
    });
