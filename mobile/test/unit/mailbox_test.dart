import 'package:bottle_crm/data/models/mailbox.dart';
import 'package:flutter_test/flutter_test.dart';

/// A mailbox as `/api/cases/mailboxes/` returns one.
Map<String, dynamic> mailboxJson({
  String id = 'm1',
  String address = 'support@acme.com',
  String provider = 'ses',
  bool isActive = true,
  bool hasTopicArn = true,
  String priority = 'Normal',
  String? caseType,
  Map<String, dynamic>? assignee,
  int casesLast30d = 4,
}) => {
  'id': id,
  'address': address,
  'provider': provider,
  'is_active': isActive,
  'has_topic_arn': hasTopicArn,
  'default_priority': priority,
  'default_case_type': caseType,
  'default_assignee': assignee,
  'cases_last_30d': casesLast30d,
  'last_received_at': '2026-08-01T09:00:00Z',
};

Map<String, dynamic> assigneeJson({bool isActive = true}) => {
  'id': 'p1',
  'is_active': isActive,
  'role': 'USER',
  'user_details': {'name': 'Ada Lovelace', 'email': 'ada@acme.com'},
};

Mailbox build([Map<String, dynamic>? json]) =>
    Mailbox.fromJson(json ?? mailboxJson());

void main() {
  group('Mailbox.fromJson', () {
    test('reads the config and the derived counts', () {
      final mailbox = build(
        mailboxJson(caseType: 'Incident', assignee: assigneeJson()),
      );
      expect(mailbox.address, 'support@acme.com');
      expect(mailbox.defaultCaseType, 'Incident');
      expect(mailbox.defaultAssignee?.displayName, 'Ada Lovelace');
      expect(mailbox.casesLast30d, 4);
    });

    test('holds the ARN an admin is sent, and never a secret', () {
      // The secret is write-only server-side so it cannot arrive. The ARN
      // arrives for an admin only, who edits it on the form.
      final json = mailboxJson()
        ..['webhook_secret'] = 'leaked'
        ..['topic_arn'] = 'arn:aws:sns:us-east-1:123456789012:acme';
      final mailbox = Mailbox.fromJson(json);
      expect(mailbox.hasTopicArn, isTrue);
      expect(mailbox.topicArn, 'arn:aws:sns:us-east-1:123456789012:acme');
      expect(mailbox.opensAs, isNot(contains('arn:aws')));
      expect(mailbox.deliveryExplanation, isNull);
    });

    test('has no ARN for a member, or for an admin whose mailbox has none', () {
      expect(build().topicArn, isNull);
      expect(
        build(mailboxJson(hasTopicArn: false)..['topic_arn'] = '').topicArn,
        isNull,
      );
    });

    test('an empty case type reads as none rather than an empty string', () {
      expect(build(mailboxJson(caseType: '')).defaultCaseType, isNull);
    });

    test('a payload with no pin field reads as unpinned, not as pinned', () {
      // Fail closed. An older payload must not draw a never-connected address
      // as one creating tickets.
      final json = mailboxJson()..remove('has_topic_arn');
      expect(Mailbox.fromJson(json).hasTopicArn, isFalse);
    });
  });

  group('delivery', () {
    test('is live only when every gate the webhook checks is clear', () {
      expect(build().delivery, MailboxDelivery.live);
      expect(build().deliveryExplanation, isNull);
    });

    test('is off when the address is turned off', () {
      expect(build(mailboxJson(isActive: false)).delivery, MailboxDelivery.off);
    });

    test('is unsupported for a provider the webhook answers 501 for', () {
      expect(
        build(mailboxJson(provider: 'imap')).delivery,
        MailboxDelivery.unsupported,
      );
    });

    test('Postmark and Mailgun are live only with a stored secret', () {
      for (final provider in ['postmark', 'mailgun']) {
        Mailbox with_(Map<String, dynamic> extra) => build(
          mailboxJson(provider: provider, hasTopicArn: false)..addAll(extra),
        );
        expect(
          with_({'has_webhook_secret': true}).delivery,
          MailboxDelivery.live,
          reason: provider,
        );
        expect(
          with_({'has_webhook_secret': false}).delivery,
          MailboxDelivery.unconfirmed,
          reason: provider,
        );
        expect(with_({}).delivery, MailboxDelivery.unconfirmed);
      }
    });

    test('a topic pin does not stand in for a secret, nor the reverse', () {
      expect(
        build(mailboxJson(provider: 'postmark')).delivery,
        MailboxDelivery.unconfirmed,
      );
      expect(
        build(
          mailboxJson(hasTopicArn: false)..['has_webhook_secret'] = true,
        ).delivery,
        MailboxDelivery.unconfirmed,
      );
    });

    test('is unconfirmed for an SES address with no topic pin', () {
      // The state neither client could see before `has_topic_arn` existed:
      // active, supported, and rejecting every notification.
      expect(
        build(mailboxJson(hasTopicArn: false)).delivery,
        MailboxDelivery.unconfirmed,
      );
    });

    test('reports the gate the webhook hits first, not every gate', () {
      expect(
        build(mailboxJson(isActive: false, provider: 'imap')).delivery,
        MailboxDelivery.off,
      );
      expect(
        build(mailboxJson(provider: 'imap', hasTopicArn: false)).delivery,
        MailboxDelivery.unsupported,
      );
    });

    test('never labels a silent address as creating tickets', () {
      for (final state in MailboxDelivery.values) {
        if (state == MailboxDelivery.live) continue;
        expect(state.label, isNot('Creating tickets'));
        expect(state.isLive, isFalse);
      }
    });
  });

  group('deliveryExplanation', () {
    test('says silence, not failure, for an address turned off', () {
      final text = build(mailboxJson(isActive: false)).deliveryExplanation!;
      expect(text, contains('silence'));
      expect(text, contains('no ticket is opened'));
    });

    test('names the provider and no longer says only SES is wired up', () {
      final text = build(mailboxJson(provider: 'imap')).deliveryExplanation!;
      expect(text, contains('IMAP'));
      expect(text, isNot(contains('Only AWS SES')));
    });

    test('asks for the webhook secret, not a topic, on Postmark', () {
      final text = build(
        mailboxJson(provider: 'postmark'),
      ).deliveryExplanation!;
      expect(text, contains('webhook secret'));
      expect(text, isNot(contains('Topic ARN')));
    });

    test(
      'says an unconfirmed address refuses mail, and both ways to pin it',
      () {
        final text = build(
          mailboxJson(hasTopicArn: false),
        ).deliveryExplanation!;
        expect(text, contains('Every message is refused'));
        expect(text, contains('an admin can enter it here'));
        expect(text, contains('from an AWS account this server allows'));
      },
    );
  });

  group('opensAs', () {
    test('names the priority, the type and where it lands', () {
      final mailbox = build(
        mailboxJson(
          priority: 'High',
          caseType: 'Incident',
          assignee: assigneeJson(),
        ),
      );
      expect(mailbox.opensAs, 'High · Incident · assigned to Ada Lovelace');
    });

    test('says routed rather than unassigned when nobody is set', () {
      // "Unassigned" would read as the end of the story. Routing runs next.
      expect(build().opensAs, 'Normal · then routed');
    });
  });

  group('deliveringMailboxCount', () {
    test('counts what opens tickets, not what is switched on', () {
      final rows = [
        build(mailboxJson(id: 'a')),
        build(mailboxJson(id: 'b', provider: 'imap')),
        build(mailboxJson(id: 'c', hasTopicArn: false)),
      ];
      expect(deliveringMailboxCount(rows), 1);
      expect(rows.where((m) => m.isActive).length, 3);
    });
  });

  group('silentMailboxes', () {
    test('is the rows that are on and creating nothing', () {
      final rows = [
        build(mailboxJson(id: 'a')),
        build(mailboxJson(id: 'b', provider: 'imap')),
        build(mailboxJson(id: 'c', hasTopicArn: false)),
        build(mailboxJson(id: 'd', isActive: false)),
      ];
      expect(silentMailboxes(rows).map((m) => m.id), ['b', 'c']);
    });
  });

  group('sortedMailboxes', () {
    test('live addresses first, then alphabetically', () {
      final rows = [
        build(mailboxJson(id: 'z', address: 'zoe@acme.com')),
        build(mailboxJson(id: 'dead', address: 'a@acme.com', isActive: false)),
        build(mailboxJson(id: 'a', address: 'alpha@acme.com')),
      ];
      expect(sortedMailboxes(rows).map((m) => m.id), ['a', 'z', 'dead']);
    });

    test('does not mutate the list it was given', () {
      final rows = [
        build(mailboxJson(id: 'dead', isActive: false)),
        build(mailboxJson(id: 'alive')),
      ];
      sortedMailboxes(rows);
      expect(rows.first.id, 'dead');
    });
  });

  group('mailboxProviderLabel', () {
    test('leaves the implemented providers alone', () {
      expect(mailboxProviderLabel('ses'), 'AWS SES');
      expect(mailboxProviderLabel('mailgun'), 'Mailgun');
      expect(mailboxProviderLabel('postmark'), 'Postmark');
    });

    test('marks the one that is not', () {
      expect(mailboxProviderLabel('imap'), 'IMAP (not wired up yet)');
      expect(supportedMailboxProviders, ['ses', 'mailgun', 'postmark']);
    });

    test('keeps every model choice offerable, marked rather than hidden', () {
      // Hiding them would silently rewrite a mailbox already set to one.
      expect(mailboxProviderLabels.keys, [
        'ses',
        'mailgun',
        'postmark',
        'imap',
      ]);
    });
  });

  group('mailboxSetupUrl', () {
    test('gives Postmark a basic-auth URL with a placeholder', () {
      expect(
        mailboxSetupUrl('postmark', 'm1', 'https://api.acme.io'),
        'https://postmark:<secret>@api.acme.io/api/cases/inbound/m1/',
      );
    });

    test('wraps the Mailgun URL in forward()', () {
      expect(
        mailboxSetupUrl('mailgun', 'm1', 'https://api.acme.io/'),
        'forward("https://api.acme.io/api/cases/inbound/m1/")',
      );
    });

    test('has none for SES, IMAP or an unknown host', () {
      expect(mailboxSetupUrl('ses', 'm1', 'https://api.acme.io'), isNull);
      expect(mailboxSetupUrl('imap', 'm1', 'https://api.acme.io'), isNull);
      expect(mailboxSetupUrl('postmark', 'm1', ''), isNull);
    });
  });

  group('webhook secret', () {
    test('has_webhook_secret is read, and a secret is never held', () {
      final json = mailboxJson(provider: 'postmark')
        ..['has_webhook_secret'] = true
        ..['webhook_secret'] = 'leaked';
      final mailbox = Mailbox.fromJson(json);
      expect(mailbox.hasWebhookSecret, isTrue);
      expect(mailbox.opensAs, isNot(contains('leaked')));
    });

    test('is sent only when typed', () {
      Map<String, dynamic> body(String? secret) => mailboxPayload(
        address: 'a@b.io',
        provider: 'postmark',
        defaultPriority: 'Normal',
        webhookSecret: secret,
      );
      expect(body(null).containsKey('webhook_secret'), isFalse);
      expect(body('   ').containsKey('webhook_secret'), isFalse);
      expect(body(' s3cret ')['webhook_secret'], 's3cret');
    });
  });

  group('mailboxPayload', () {
    test('sends the config and nothing the server owns', () {
      final body = mailboxPayload(
        address: '  Support@ACME.com ',
        provider: 'ses',
        defaultPriority: 'High',
        defaultCaseType: 'Incident',
        defaultAssigneeId: 'p1',
        isActive: true,
      );
      expect(body['address'], 'support@acme.com');
      expect(body.containsKey('webhook_secret'), isFalse);
      expect(body.containsKey('topic_arn'), isFalse);
      expect(body.containsKey('org'), isFalse);
    });

    test('sends a topic ARN only when given one, trimmed; empty clears', () {
      Map<String, dynamic> withArn(String? arn) => mailboxPayload(
        address: 'a@b.com',
        provider: 'ses',
        defaultPriority: 'Normal',
        topicArn: arn,
      );
      expect(
        withArn(' arn:aws:sns:us-east-1:123456789012:x ')['topic_arn'],
        'arn:aws:sns:us-east-1:123456789012:x',
      );
      expect(withArn('')['topic_arn'], '');
      expect(withArn(null).containsKey('topic_arn'), isFalse);
    });

    test('clears the nullable pair with null, never the empty string', () {
      // `''` fails the ChoiceField and the PK lookup alike; both are
      // `allow_null=True`, so null is what clears them.
      final body = mailboxPayload(
        address: 'a@b.com',
        provider: 'ses',
        defaultPriority: 'Normal',
        defaultCaseType: '',
        defaultAssigneeId: '',
      );
      expect(body['default_case_type'], isNull);
      expect(body['default_assignee_id'], isNull);
    });

    test('omits is_active entirely when the form does not own it', () {
      final body = mailboxPayload(
        address: 'a@b.com',
        provider: 'ses',
        defaultPriority: 'Normal',
      );
      expect(body.containsKey('is_active'), isFalse);
    });
  });

  group('mailboxTopicArnEdit', () {
    const arn = 'arn:aws:sns:us-east-1:123456789012:inbound';

    test('is null when the field still holds what it was prefilled with', () {
      // A stale form must not undo a pin the webhook set after it opened.
      expect(mailboxTopicArnEdit('', null), isNull);
      expect(mailboxTopicArnEdit(' $arn ', arn), isNull);
    });

    test('is the new value, trimmed, when the admin changed it', () {
      expect(mailboxTopicArnEdit(' $arn', null), arn);
      expect(
        mailboxTopicArnEdit('arn:aws:sns:eu-west-1:123456789012:other', arn),
        'arn:aws:sns:eu-west-1:123456789012:other',
      );
    });

    test('is the empty string when the admin cleared it', () {
      expect(mailboxTopicArnEdit('  ', arn), '');
    });
  });

  group('mailboxActivePayload', () {
    test('carries the one key, so a save cannot rewrite the address', () {
      expect(mailboxActivePayload(true), {'is_active': true});
      expect(mailboxActivePayload(false), {'is_active': false});
    });
  });

  group('mailboxAddressProblem', () {
    test('accepts an ordinary address', () {
      expect(mailboxAddressProblem('support@acme.com'), isNull);
    });

    test('refuses an empty one', () {
      expect(mailboxAddressProblem('   '), isNotNull);
    });

    test('refuses something that is not an address', () {
      expect(mailboxAddressProblem('support'), isNotNull);
      expect(mailboxAddressProblem('@acme.com'), isNotNull);
      expect(mailboxAddressProblem('support@'), isNotNull);
      expect(mailboxAddressProblem('a b@acme.com'), isNotNull);
    });

    test('does not out-guess EmailField on the odd but legal ones', () {
      // A stricter pattern here would refuse addresses the server accepts.
      expect(mailboxAddressProblem('support+tickets@acme.co.uk'), isNull);
      expect(mailboxAddressProblem("o'brien@acme.com"), isNull);
    });
  });

  group('the copy that says what is true', () {
    test('the auth note names both SES checks and the stored secret', () {
      expect(mailboxAuthExplanation, contains('signs each notification'));
      expect(mailboxAuthExplanation, contains('pinned'));
      expect(mailboxAuthExplanation, contains('Topic ARN'));
      expect(
        mailboxAuthExplanation,
        contains('AWS account this server allows'),
      );
      expect(mailboxAuthExplanation, contains('webhook secret'));
    });

    test('deleting says the pin goes with it', () {
      expect(mailboxDeleteExplanation, contains('topic pin goes with it'));
    });

    test('turning off says mail keeps arriving', () {
      expect(mailboxDeactivateExplanation, contains('Mail keeps arriving'));
      expect(mailboxDeactivateExplanation, contains('nothing bounces'));
    });
  });
}
