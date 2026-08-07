/// Pulling a list out of a response body, whatever the endpoint calls it.
///
/// The API has no single list envelope. `/api/contacts/` publishes `results`,
/// `/api/users/get-teams-and-users/` publishes `profiles` and `teams`, and
/// `/api/accounts/` nests its rows two deep under
/// `active_accounts.open_accounts`. Each caller used to guess with a chain of
/// `if (data['x'] != null)`, which fails silently: a wrong guess yields an
/// empty list and a picker with nothing in it, not an error anyone sees.
///
/// Passing the paths explicitly keeps the guess in one place and makes it
/// testable against the real shape.
library;

/// The first list found at any of [paths], or `[]` if none matched.
///
/// A path is dot-separated and may descend through nested maps, so
/// `'active_accounts.open_accounts'` is valid. Order matters: the first path
/// that resolves to a list wins, so put the endpoint's real key first and any
/// tolerated alternatives after it.
List<Map<String, dynamic>> listFromEnvelope(
  Map<String, dynamic> data,
  List<String> paths,
) {
  for (final path in paths) {
    dynamic node = data;
    for (final segment in path.split('.')) {
      if (node is Map<String, dynamic> && node.containsKey(segment)) {
        node = node[segment];
      } else {
        node = null;
        break;
      }
    }
    if (node is List) {
      return node.whereType<Map<String, dynamic>>().toList();
    }
  }
  return const [];
}
