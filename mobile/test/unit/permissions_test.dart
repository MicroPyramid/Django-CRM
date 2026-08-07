import 'package:bottle_crm/core/permissions.dart';
import 'package:flutter_test/flutter_test.dart';

/// The rule under test mirrors `LeadDetailView.delete` and
/// `OpportunityDetailView.delete`: admins and the record's creator, nobody
/// else. Assignment grants read and edit there, never delete, so the assignee
/// case below is the one that matters and the one the app used to get wrong.
void main() {
  group('isAdminOrOwner', () {
    test('an admin may delete a record someone else created', () {
      expect(
        isAdminOrOwner(
          isAdmin: true,
          currentUserKey: 'admin@example.com',
          ownerKey: 'someone.else@example.com',
        ),
        isTrue,
      );
    });

    test('a member may delete their own record', () {
      expect(
        isAdminOrOwner(
          isAdmin: false,
          currentUserKey: 'member@example.com',
          ownerKey: 'member@example.com',
        ),
        isTrue,
      );
    });

    test('a member may not delete a record someone else created', () {
      expect(
        isAdminOrOwner(
          isAdmin: false,
          currentUserKey: 'member@example.com',
          ownerKey: 'admin@example.com',
        ),
        isFalse,
      );
    });

    test('the comparison ignores case and surrounding whitespace', () {
      expect(
        isAdminOrOwner(
          isAdmin: false,
          currentUserKey: 'Member@Example.com',
          ownerKey: '  member@example.com ',
        ),
        isTrue,
      );
    });

    test('an unknown creator hides the action from a member', () {
      expect(
        isAdminOrOwner(
          isAdmin: false,
          currentUserKey: 'member@example.com',
          ownerKey: null,
        ),
        isFalse,
      );
      expect(
        isAdminOrOwner(
          isAdmin: false,
          currentUserKey: 'member@example.com',
          ownerKey: '',
        ),
        isFalse,
      );
    });

    test('an unknown creator does not block an admin', () {
      expect(
        isAdminOrOwner(isAdmin: true, currentUserKey: null, ownerKey: null),
        isTrue,
      );
    });

    test('an unknown current user hides the action', () {
      expect(
        isAdminOrOwner(
          isAdmin: false,
          currentUserKey: null,
          ownerKey: 'someone@example.com',
        ),
        isFalse,
      );
    });
  });
}
