import 'package:bottle_crm/data/models/lookup_models.dart';
import 'package:bottle_crm/widgets/common/mention_text.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('mentionTokens', () {
    const handles = {'liz.rao', 'sam'};
    List<(String, bool)> read(String body) => [
      for (final t in mentionTokens(body, handles)) (t.text, t.isMention),
    ];

    test('marks a handle that names a member', () {
      expect(read('Thanks @liz.rao, done'), [
        ('Thanks ', false),
        ('@liz.rao', true),
        (', done', false),
      ]);
    });

    test('matches a handle whatever its case', () {
      expect(read('@LIZ.RAO'), [('@LIZ.RAO', true)]);
    });

    test('leaves an unknown handle as text', () {
      expect(read('cc @bob'), [('cc ', false), ('@bob', false)]);
    });

    test('leaves an email address alone', () {
      expect(read('mail liz.rao@acme.com'), [('mail liz.rao@acme.com', false)]);
    });

    test(
      'reads a trailing full stop as part of the handle, as the backend does',
      () {
        // cases/notifications.py captures "liz.rao." and resolves nobody.
        expect(read('Thanks @liz.rao.'), [
          ('Thanks ', false),
          ('@liz.rao.', false),
        ]);
      },
    );
  });

  test(
    "mentionHandles uses each active member's email local part, lower-cased",
    () {
      const users = [
        UserLookup(
          id: '1',
          email: 'Liz.Rao@acme.com',
          role: 'USER',
          isActive: true,
        ),
        UserLookup(
          id: '2',
          email: 'gone@acme.com',
          role: 'USER',
          isActive: false,
        ),
      ];
      expect(mentionHandles(users), {'liz.rao'});
    },
  );

  testWidgets('draws a known handle as a chip and leaves the rest plain', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: MentionText('Ask @sam or @bob', handles: {'sam'})),
      ),
    );

    final root = tester.widget<Text>(find.byType(Text)).textSpan! as TextSpan;
    final spans = root.children!.cast<TextSpan>();
    final sam = spans.firstWhere((s) => s.text == '@sam');
    final bob = spans.firstWhere((s) => s.text == '@bob');
    expect(sam.style?.fontWeight, FontWeight.w600);
    expect(sam.style?.backgroundColor, isNotNull);
    expect(bob.style, isNull);
    expect(find.text('Ask @sam or @bob', findRichText: true), findsOneWidget);
  });
}
