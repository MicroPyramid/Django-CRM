/// Lead sources: the org's own list, which an admin edits.
///
/// A lead, contact or deal stores a source's [LeadSource.key] and nothing
/// else, so a label is always looked up. A stored key this app does not know
/// is kept exactly as the server sent it and is sent back only when the user
/// picks another source.
library;

class LeadSource {
  const LeadSource({
    this.id = '',
    required this.key,
    required this.label,
    this.isActive = true,
    this.order = 0,
  });

  /// Empty for the fixed lists below and for a stored key the list lacks.
  final String id;
  final String key;
  final String label;

  /// A retired source stays on the records that have it and cannot be picked
  /// for new ones. Sources are never deleted.
  final bool isActive;
  final int order;

  factory LeadSource.fromJson(Map<String, dynamic> json) => LeadSource(
    id: json['id']?.toString() ?? '',
    key: json['key']?.toString() ?? '',
    label: json['label']?.toString() ?? '',
    isActive: json['is_active'] as bool? ?? true,
    order: (json['order'] as num?)?.toInt() ?? 0,
  );

  /// A stored key that is not in the list being offered.
  bool get isUnlisted => id.isEmpty && !isActive;

  String get pickerLabel => isActive || isUnlisted ? label : '$label (retired)';
}

/// What an API older than editable sources accepts on a lead: its seven fixed
/// values, including the stored misspelling `compaign`.
const List<LeadSource> legacyLeadSources = [
  LeadSource(key: 'call', label: 'Call'),
  LeadSource(key: 'email', label: 'Email'),
  LeadSource(key: 'existing customer', label: 'Existing customer'),
  LeadSource(key: 'partner', label: 'Partner'),
  LeadSource(key: 'public relations', label: 'Public relations'),
  LeadSource(key: 'compaign', label: 'Campaign'),
  LeadSource(key: 'other', label: 'Other'),
];

/// The same API's deal values, a separate uppercase list.
const List<LeadSource> legacyDealSources = [
  LeadSource(key: 'CALL', label: 'Call'),
  LeadSource(key: 'EMAIL', label: 'Email'),
  LeadSource(key: 'EXISTING CUSTOMER', label: 'Existing customer'),
  LeadSource(key: 'PARTNER', label: 'Partner'),
  LeadSource(key: 'PUBLIC RELATIONS', label: 'Public relations'),
  LeadSource(key: 'CAMPAIGN', label: 'Campaign'),
  LeadSource(key: 'WEBSITE', label: 'Website'),
  LeadSource(key: 'OTHER', label: 'Other'),
];

/// The label for [key]: from [sources] first, then the fixed lists, else the
/// key itself, as the web shows it.
String leadSourceLabel(String key, [Iterable<LeadSource> sources = const []]) {
  if (key.isEmpty) return '';
  for (final s in sources) {
    if (s.key == key) return s.label;
  }
  final lower = key.toLowerCase();
  for (final s in [...legacyLeadSources, ...legacyDealSources]) {
    if (s.key.toLowerCase() == lower) return s.label;
  }
  return key;
}

/// What a picker offers: every active source in [sources], plus [current]
/// when it is retired or not listed at all, so a form never drops it.
List<LeadSource> pickableSources(List<LeadSource> sources, String current) {
  final out = sources.where((s) => s.isActive).toList();
  if (current.isEmpty || out.any((s) => s.key == current)) return out;
  final stored = sources.where((s) => s.key == current).firstOrNull;
  out.add(
    stored ??
        LeadSource(
          key: current,
          label: leadSourceLabel(current, sources),
          isActive: false,
        ),
  );
  return out;
}

/// `GET /api/leads/sources/`, or the fixed list of an API that predates it.
class LeadSourcesAnswer {
  const LeadSourcesAnswer({required this.sources, this.offered = true});

  /// The API answered 404: its sources are the seven fixed ones and cannot be
  /// edited, and leads carry no sub-source or reference there.
  const LeadSourcesAnswer.legacy()
    : sources = legacyLeadSources,
      offered = false;

  /// In the server's order, retired ones included.
  final List<LeadSource> sources;
  final bool offered;

  String labelFor(String key) => leadSourceLabel(key, sources);

  List<LeadSource> pickable(String current) =>
      pickableSources(sources, current);

  /// A deal's picker. An older API keeps deals on their own uppercase list.
  List<LeadSource> pickableForDeal(String current) =>
      pickableSources(offered ? sources : legacyDealSources, current);

  String dealLabelFor(String key) =>
      leadSourceLabel(key, offered ? sources : legacyDealSources);
}
