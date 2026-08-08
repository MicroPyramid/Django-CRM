/// A saved reply, from `MacroSerializer`.
///
/// Two scopes with genuinely different rules, and the difference is not
/// cosmetic. An `org` macro is shared, admin-managed, and `DELETE` only turns
/// it off. A `personal` macro belongs to one person and `DELETE` removes it for
/// good. Both go through the same endpoint and the server decides which
/// happens from the row's own scope, so the client's only job is to say the
/// right thing before asking.
class Macro {
  const Macro({
    required this.id,
    this.title = '',
    this.body = '',
    this.scope = scopeOrg,
    this.ownerEmail,
    this.isActive = true,
    this.usageCount = 0,
    this.unknownPlaceholders = const [],
  });

  static const String scopeOrg = 'org';
  static const String scopePersonal = 'personal';

  final String id;
  final String title;
  final String body;
  final String scope;

  /// `owner_name`, which the serializer fills from the owner's email because
  /// `User` carries no display name. Null on an org macro, which has no owner.
  final String? ownerEmail;

  final bool isActive;
  final int usageCount;

  /// `%token%` placeholders the server's renderer does not expand, computed
  /// server-side by `find_unknown_placeholders`.
  ///
  /// Passed through rather than recomputed. Recomputing here would mean this
  /// app deciding which tokens are broken, and it would drift from the set the
  /// renderer actually expands the first time either changed. Unknown tokens
  /// are not a save-blocker: they render literally into the reply, which is
  /// why a macro carrying one is worth flagging.
  final List<String> unknownPlaceholders;

  bool get isPersonal => scope == scopePersonal;

  /// "Everyone" / "Just you", matching `MACRO_SCOPE_LABEL` in
  /// `frontend/src/lib/v2/enums.js`.
  String get scopeLabel => isPersonal ? 'Just you' : 'Everyone';

  factory Macro.fromJson(Map<String, dynamic> json) {
    final unknown = json['unknown_placeholders'];
    return Macro(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      scope: json['scope']?.toString() ?? scopeOrg,
      ownerEmail: (json['owner_name'] as String?)?.trim().isEmpty ?? true
          ? null
          : json['owner_name'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      usageCount: json['usage_count'] as int? ?? 0,
      unknownPlaceholders: unknown is List
          ? unknown.map((t) => t.toString()).toList(growable: false)
          : const [],
    );
  }
}

/// Whether the signed-in user may edit or remove this macro.
///
/// Mirrors `MacroDetailView._get_writable`, which is the only authority: an
/// org macro needs an admin, a personal macro needs its owner, and an admin
/// gets no exception on someone else's personal macro (that answers 404, not
/// 403, so the id space cannot be used to discover whose private macros
/// exist).
///
/// Ownership is compared on email rather than assumed from the list. The list
/// endpoint does already exclude other people's personal macros, so today
/// every personal row belongs to the caller, but that is a property of the
/// query and this is a rule about the row. Deriving one from the other would
/// put an authorization answer at the mercy of a filter change.
///
/// Returns false when either email is unknown, so an unparsed payload hides
/// the action rather than offering a write that answers 404.
bool canWriteMacro({
  required bool isAdmin,
  required String scope,
  required String? ownerEmail,
  required String? myEmail,
}) {
  if (scope == Macro.scopeOrg) return isAdmin;
  final owner = ownerEmail?.trim().toLowerCase();
  final me = myEmail?.trim().toLowerCase();
  if (owner == null || owner.isEmpty || me == null || me.isEmpty) return false;
  return owner == me;
}

/// What removing this macro actually does, in the words the confirm dialog
/// needs.
///
/// `MacroDetailView.delete` soft-deletes an org macro (`is_active` flips, the
/// row stays and stays counted) and hard-deletes a personal one. One endpoint,
/// two outcomes, decided server-side. A dialog that says "Delete" over a soft
/// delete, or "Turn off" over a permanent one, is the same defect either way.
class MacroRemoval {
  const MacroRemoval({
    required this.actionLabel,
    required this.title,
    required this.detail,
    required this.isPermanent,
  });

  final String actionLabel;
  final String title;
  final String detail;
  final bool isPermanent;
}

MacroRemoval macroRemoval(Macro macro) {
  if (macro.isPersonal) {
    return MacroRemoval(
      actionLabel: 'Delete',
      title: 'Delete ${macro.title}?',
      detail:
          'This is one of your own saved replies, so it is removed for '
          'good. Nobody else could see it.',
      isPermanent: true,
    );
  }
  return MacroRemoval(
    actionLabel: 'Turn off',
    title: 'Turn off ${macro.title}?',
    detail:
        'It stops being offered in the reply box for everyone. The saved '
        'reply is kept and you can turn it back on.',
    isPermanent: false,
  );
}

/// What a macro form has to say before it can be submitted, or `null`.
///
/// `MacroSerializer` requires both `title` and `body`, and
/// `_resolve_scope_and_owner` rejects any scope outside the two. This is a
/// fast fail so a blank body does not cost a round trip.
String? validateMacroDraft({
  required String title,
  required String body,
  required String scope,
}) {
  if (title.trim().isEmpty) return 'Give the saved reply a title.';
  if (body.trim().isEmpty) return 'A saved reply needs something to say.';
  if (scope != Macro.scopeOrg && scope != Macro.scopePersonal) {
    return 'Choose who this reply is for.';
  }
  return null;
}

/// The body for `POST /macros/` and `PATCH /macros/<id>/`.
///
/// `owner` is absent and must stay absent. It is `read_only` on the serializer
/// and re-derived by `_resolve_scope_and_owner` from `request.profile`; a
/// client that could name one could file a saved reply as somebody else.
/// `org` is a JWT claim for the same reason. `usage_count` is server-owned.
Map<String, dynamic> macroPayload({
  required String title,
  required String body,
  required String scope,
}) {
  return {'title': title.trim(), 'body': body.trim(), 'scope': scope};
}

/// The body for turning an org macro back on.
///
/// Only `is_active`, and it goes as a PATCH. Reusing [macroPayload] would need
/// a title and a body the reactivate control does not have. `_get_writable`
/// still applies, so a non-admin reactivating an org macro is refused.
Map<String, dynamic> macroActivatePayload() => {'is_active': true};
