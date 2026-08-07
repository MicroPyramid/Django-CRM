import 'package:flutter/foundation.dart';
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

/// How many rows a picker asks for.
///
/// Every paginated list endpoint here uses DRF's `LimitOffsetPagination` with
/// `PAGE_SIZE = 10`, so a lookup that sent no `limit` offered ten rows and no
/// hint that there were more. Confirmed against the seeded org: `/api/contacts/`
/// answered `contacts_count: 15` beside ten rows, and five contacts could not be
/// picked on any form in the app. Tags were 10 of 14.
///
/// 500 is a cap rather than a fix. An org past it still cannot pick everything,
/// and the real answer is a searching picker backed by the server. This number
/// is what makes the gap rare instead of routine.
const int lookupPageLimit = 500;

/// The URL a lookup actually requests. Public only so a test can assert the
/// limit is on it: without one every picker in the app silently offers ten rows.
@visibleForTesting
String lookupUrl(String url) => Uri.parse(
  url,
).replace(queryParameters: {'limit': '$lookupPageLimit'}).toString();

/// Accounts
class AccountsLookupNotifier extends AsyncNotifier<List<AccountLookup>> {
  @override
  Future<List<AccountLookup>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<List<AccountLookup>> _fetch() async {
    final response = await _apiService.get(lookupUrl(ApiConfig.accounts));
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
    final response = await _apiService.get(lookupUrl(ApiConfig.contacts));
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
    return listFromEnvelope(response.data!, const [
      'profiles',
    ]).map(UserLookup.fromJson).where((u) => u.isActive).toList();
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
    final response = await _apiService.get(lookupUrl(ApiConfig.tags));
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

/// The three records a task can be attached to that are not accounts.
///
/// Each has a full module provider already, and the task form used to read
/// those. It could not: they page (20 rows) and they carry whatever search and
/// filters their list screen last applied, so a task form opened after filtering
/// deals to Won offered only won deals, and a task form opened on a cold app
/// offered nothing at all with the message "Open this section on the web or
/// create one first."
class _EntityLookupNotifier extends AsyncNotifier<List<EntityLookup>> {
  _EntityLookupNotifier({
    required this.url,
    required this.paths,
    required this.parse,
    required this.what,
  });

  final String url;
  final List<String> paths;
  final EntityLookup Function(Map<String, dynamic>) parse;
  final String what;

  @override
  Future<List<EntityLookup>> build() => _fetch();

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(_fetch);
  }

  Future<List<EntityLookup>> _fetch() async {
    final response = await _apiService.get(lookupUrl(url));
    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load $what');
    }
    return listFromEnvelope(response.data!, paths).map(parse).toList();
  }
}

/// Leads. Rows are nested under `open_leads.open_leads`, the same shape trap the
/// accounts lookup hit. Closed leads sit under `close_leads` and are not offered.
final leadsLookupProvider =
    AsyncNotifierProvider<_EntityLookupNotifier, List<EntityLookup>>(
      () => _EntityLookupNotifier(
        url: ApiConfig.leads,
        paths: const ['open_leads.open_leads'],
        parse: (json) => EntityLookup.person(
          json,
          fallbackKeys: const ['email', 'company_name'],
        ),
        what: 'leads',
      ),
    );

final opportunitiesLookupProvider =
    AsyncNotifierProvider<_EntityLookupNotifier, List<EntityLookup>>(
      () => _EntityLookupNotifier(
        url: ApiConfig.opportunities,
        paths: const ['opportunities'],
        parse: (json) => EntityLookup.fromJson(json, labelKeys: const ['name']),
        what: 'deals',
      ),
    );

final ticketsLookupProvider =
    AsyncNotifierProvider<_EntityLookupNotifier, List<EntityLookup>>(
      () => _EntityLookupNotifier(
        url: ApiConfig.tickets,
        paths: const ['cases'],
        parse: (json) => EntityLookup.fromJson(json, labelKeys: const ['name']),
        what: 'tickets',
      ),
    );

/// Convenience wrappers. Return the resolved list (or empty during
/// load/error). Forms that don't care about loading state watch these.
/// Picker options, resolved. Named for what they are rather than for the
/// resource, because `accountsProvider` now belongs to the accounts module and
/// two providers a letter apart would be a trap.
final accountOptionsProvider = Provider<List<AccountLookup>>((ref) {
  return ref.watch(accountsLookupProvider).value ?? const [];
});

final contactOptionsProvider = Provider<List<ContactLookup>>((ref) {
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

/// The four kinds a task can be attached to, in one shape.
///
/// These keep the `AsyncValue` rather than flattening to a list like the
/// wrappers above, because the picker that reads them has to tell "still
/// loading" apart from "this org has none". Flattening is what made a cold app
/// claim there was nothing to link to.
final accountEntityOptionsProvider = Provider<AsyncValue<List<EntityLookup>>>((
  ref,
) {
  return ref
      .watch(accountsLookupProvider)
      .whenData(
        (accounts) => [
          for (final account in accounts)
            EntityLookup(id: account.id, label: account.name),
        ],
      );
});

final leadEntityOptionsProvider = Provider<AsyncValue<List<EntityLookup>>>(
  (ref) => ref.watch(leadsLookupProvider),
);

final opportunityEntityOptionsProvider =
    Provider<AsyncValue<List<EntityLookup>>>(
      (ref) => ref.watch(opportunitiesLookupProvider),
    );

final ticketEntityOptionsProvider = Provider<AsyncValue<List<EntityLookup>>>(
  (ref) => ref.watch(ticketsLookupProvider),
);

/// Custom field definitions, keyed by target_model (Case, Lead, ...).
///
/// Each form watches the family for its entity; results are cached per-target
/// for the lifetime of the provider scope so reopening the same form is cheap.
///
/// `include_counts=false` matters. Without it the endpoint also computes
/// `records_missing_value` for every definition the org has, which is one
/// COUNT over the org's records per target model plus a
/// `custom_fields ? key` scan per field. A form that only wants labels and
/// types does not need those numbers, and paying for them on every lead, deal
/// and task form open puts full scans on the record path. The settings screen
/// is the one caller that wants them and asks separately.
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
              'include_counts': 'false',
            },
          )
          .toString();
      final response = await _apiService.get(url);
      if (!response.success || response.data == null) {
        throw Exception(response.message ?? 'Failed to load custom fields');
      }
      final parsed = listFromEnvelope(response.data!, const [
        'definitions',
      ]).map(CustomFieldDefinition.fromJson).toList();
      parsed.sort((a, b) {
        final byOrder = a.displayOrder.compareTo(b.displayOrder);
        return byOrder != 0 ? byOrder : a.label.compareTo(b.label);
      });
      return parsed;
    });
