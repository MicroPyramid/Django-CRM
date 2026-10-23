import 'package:flutter/widgets.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';

import '../../data/models/org_module.dart';

/// One slot of the bottom bar. The "More" slot opens a sheet instead of
/// switching branches, and lists every branch it stands for so the tab
/// highlights on any of them.
class NavEntry {
  final String label;
  final IconData icon;
  final List<int> branches;
  final bool opensSheet;
  const NavEntry({
    required this.label,
    required this.icon,
    required this.branches,
    this.opensSheet = false,
  });
}

const _home = NavEntry(
  label: 'Home',
  icon: LucideIcons.layoutDashboard,
  branches: [0],
);

// In bar order, each with the module that switches it off.
const _candidates = <(String, NavEntry)>[
  ('leads', NavEntry(label: 'Leads', icon: LucideIcons.users, branches: [1])),
  (
    'deals',
    NavEntry(label: 'Deals', icon: LucideIcons.briefcase, branches: [2]),
  ),
  (
    'tickets',
    NavEntry(label: 'Tickets', icon: LucideIcons.ticket, branches: [3]),
  ),
  (
    'tasks',
    NavEntry(label: 'Tasks', icon: LucideIcons.checkSquare, branches: [4]),
  ),
];

bool _on(OrgModulesAnswer? modules, String key) =>
    modules == null || modules.isOn(key);

List<NavEntry> _barModules(OrgModulesAnswer? modules) => [
  for (final c in _candidates)
    if (_on(modules, c.$1)) c.$2,
].take(3).toList();

/// Tasks is on but has no slot in the bar, so it lives behind More.
bool tasksBehindMore(OrgModulesAnswer? modules) =>
    _on(modules, 'tasks') &&
    !_barModules(modules).any((e) => e.branches[0] == 4);

/// Home, the first three switched-on of Leads, Deals, Tickets and Tasks, then
/// More. With a null answer (nothing known) every module is on.
List<NavEntry> navEntries(OrgModulesAnswer? modules) => [
  _home,
  ..._barModules(modules),
  NavEntry(
    label: 'More',
    icon: LucideIcons.moreHorizontal,
    branches: [5, if (tasksBehindMore(modules)) 4],
    opensSheet: true,
  ),
];
