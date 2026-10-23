import 'package:bottle_crm/widgets/common/nav_entries.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/modules_fixtures.dart';

List<String> _labels(List<String> off) => [
  for (final e in navEntries(modulesAnswer(off: off))) e.label,
];

void main() {
  test('the default bar is Home, Leads, Deals, Tickets, More', () {
    for (final answer in [null, modulesAnswer()]) {
      final entries = navEntries(answer);
      expect(
        [for (final e in entries) e.label],
        ['Home', 'Leads', 'Deals', 'Tickets', 'More'],
      );
      expect(
        [for (final e in entries) e.branches],
        [
          [0],
          [1],
          [2],
          [3],
          [5, 4],
        ],
      );
      expect(entries.last.opensSheet, isTrue);
      expect(tasksBehindMore(answer), isTrue);
    }
  });

  test('Tasks takes the slot of an off module, and More then holds only '
      'branch 5', () {
    expect(_labels(['deals']), ['Home', 'Leads', 'Tickets', 'Tasks', 'More']);
    final entries = navEntries(modulesAnswer(off: ['tickets']));
    expect(
      [for (final e in entries) e.branches],
      [
        [0],
        [1],
        [2],
        [4],
        [5],
      ],
    );
    expect(tasksBehindMore(modulesAnswer(off: ['tickets'])), isFalse);
  });

  test('a switched-off Tasks is never in the bar or behind More', () {
    final answer = modulesAnswer(off: ['tasks']);
    expect(_labels(['tasks']), ['Home', 'Leads', 'Deals', 'Tickets', 'More']);
    expect(navEntries(answer).last.branches, [5]);
    expect(tasksBehindMore(answer), isFalse);
  });

  test('with only one of the four on, the bar shrinks and More stays last', () {
    final off = ['leads', 'deals', 'tickets'];
    expect(_labels(off), ['Home', 'Tasks', 'More']);
    expect(_labels(['leads', 'deals', 'tickets', 'tasks']), ['Home', 'More']);
  });
}
