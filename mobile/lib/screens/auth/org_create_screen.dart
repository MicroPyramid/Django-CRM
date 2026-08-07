import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../config/api_config.dart';
import '../../providers/auth_provider.dart';
import '../../routes/app_router.dart';
import '../../services/api_service.dart';
import '../../widgets/forms/unsaved_changes.dart';

/// Creating an organization from the phone.
///
/// Until now this only existed on the web, while the org picker's empty state
/// told people to "create a new organization" and gave them no way to. A user
/// who signed in here before anyone had invited them reached a screen whose
/// only working control was Sign Out.
class OrgCreateScreen extends ConsumerStatefulWidget {
  const OrgCreateScreen({super.key});

  @override
  ConsumerState<OrgCreateScreen> createState() => _OrgCreateScreenState();
}

class _OrgCreateScreenState extends ConsumerState<OrgCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();

  /// `{name, offsetMinutes}` from `/api/org/timezones/`. Fetched rather than
  /// built on the device: the server validates against its own tz database, and
  /// a name this app invented could be rejected or, worse, stored as a
  /// different spelling of the same zone.
  List<_Zone> _zones = const [];
  String _timezone = 'UTC';
  bool _loadingZones = true;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _loadZones();
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _loadZones() async {
    final response = await ApiService().get(ApiConfig.timezones);
    if (!mounted) return;

    // Not written as a single ternary: `cond ? map?['k'] : null` makes the
    // Dart parser read the null-aware index as the conditional's own `?`.
    var zones = const <_Zone>[];
    if (response.success) {
      final raw = response.data?['timezones'];
      if (raw is List) {
        zones = raw
            .whereType<Map<String, dynamic>>()
            .map(_Zone.fromJson)
            .toList(growable: false);
      }
    }

    setState(() {
      _zones = zones;
      _timezone = _bestGuess(zones);
      _loadingZones = false;
    });
  }

  /// The device cannot name its own IANA zone without a platform package, but
  /// it always knows its current offset from UTC, and that narrows 490 choices
  /// to a handful. The first match is a guess, clearly editable, and far better
  /// than starting an Indian user at Africa/Abidjan.
  String _bestGuess(List<_Zone> zones) {
    if (zones.isEmpty) return 'UTC';
    final deviceOffset = DateTime.now().timeZoneOffset.inMinutes;
    for (final zone in zones) {
      if (zone.offsetMinutes == deviceOffset) return zone.name;
    }
    return zones.any((z) => z.name == 'UTC') ? 'UTC' : zones.first.name;
  }

  Future<void> _submit() async {
    if (_submitting) return;
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() => _submitting = true);
    final failure = await ref
        .read(authProvider.notifier)
        .createOrganization(_nameController.text.trim(), timezone: _timezone);

    if (!mounted) return;
    setState(() => _submitting = false);

    if (failure != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(failure), backgroundColor: Colors.red),
      );
      return;
    }
    context.go(AppRoutes.dashboard);
  }

  /// The timezone is a guess the screen made, not something the user typed,
  /// so only a name counts as work worth keeping.
  bool get _hasUnsavedChanges => _nameController.text.trim().isNotEmpty;

  @override
  Widget build(BuildContext context) {
    return UnsavedChangesGuard(
      hasUnsavedChanges: () => _hasUnsavedChanges,
      isSaving: _submitting,
      child: Scaffold(
        backgroundColor: Colors.grey[50],
        appBar: AppBar(
          title: const Text('New Organization'),
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 0,
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextFormField(
                    controller: _nameController,
                    autofocus: true,
                    textCapitalization: TextCapitalization.words,
                    enabled: !_submitting,
                    decoration: const InputDecoration(
                      labelText: 'Organization name',
                      hintText: 'e.g. Acme Inc.',
                      border: OutlineInputBorder(),
                    ),
                    validator: (value) {
                      final name = value?.trim() ?? '';
                      if (name.isEmpty) return 'Give the organization a name';
                      // Mirrors the server's `validate_name`, which is the rule
                      // that actually decides. This only saves a round trip.
                      if (RegExp(
                        r'''[~!@#$%^&*()+{}":;'/\[\]]''',
                      ).hasMatch(name)) {
                        return 'Letters, numbers, spaces, hyphens and dots only';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 20),
                  if (_loadingZones)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8),
                      child: LinearProgressIndicator(),
                    )
                  else
                    DropdownButtonFormField<String>(
                      initialValue: _timezone,
                      isExpanded: true,
                      decoration: const InputDecoration(
                        labelText: 'Time zone',
                        border: OutlineInputBorder(),
                      ),
                      items: _zones
                          .map(
                            (zone) => DropdownMenuItem(
                              value: zone.name,
                              child: Text(
                                zone.label,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          )
                          .toList(),
                      onChanged: _submitting
                          ? null
                          : (value) {
                              if (value != null) {
                                setState(() => _timezone = value);
                              }
                            },
                    ),
                  const SizedBox(height: 6),
                  Text(
                    'Sets when a day starts here, so "due today" and "overdue" '
                    'mean what your team expects. You can change it later in '
                    'Settings.',
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: _submitting ? null : _submit,
                      child: _submitting
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Create organization'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Zone {
  const _Zone({required this.name, required this.offsetMinutes});

  final String name;
  final int offsetMinutes;

  factory _Zone.fromJson(Map<String, dynamic> json) => _Zone(
    name: json['name'] as String? ?? 'UTC',
    offsetMinutes: (json['offset_minutes'] as num?)?.toInt() ?? 0,
  );

  /// "Asia/Kolkata (UTC+05:30)". The offset is what makes a 490-entry list
  /// readable; the name alone tells most people very little.
  String get label {
    final pretty = name.replaceAll('_', ' ');
    if (offsetMinutes == 0) return '$pretty (UTC)';
    final sign = offsetMinutes < 0 ? '-' : '+';
    final abs = offsetMinutes.abs();
    final hh = (abs ~/ 60).toString().padLeft(2, '0');
    final mm = (abs % 60).toString().padLeft(2, '0');
    return '$pretty (UTC$sign$hh:$mm)';
  }
}
