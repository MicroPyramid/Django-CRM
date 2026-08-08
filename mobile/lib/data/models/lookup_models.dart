// Lookup models for deal form selectors
// These are simplified models used for dropdowns and multi-selects

/// Account model for selector
class AccountLookup {
  final String id;
  final String name;
  final String? website;
  final String? phone;

  const AccountLookup({
    required this.id,
    required this.name,
    this.website,
    this.phone,
  });

  factory AccountLookup.fromJson(Map<String, dynamic> json) {
    return AccountLookup(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      website: json['website'] as String?,
      phone: json['phone'] as String?,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is AccountLookup &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Contact model for selector
class ContactLookup {
  final String id;
  final String firstName;
  final String lastName;
  final String? email;
  final String? phone;

  /// The `account` FK, from `account_detail`, NOT the `Account.contacts` M2M.
  ///
  /// The FK is the one the invoice serializer cross-checks ("Contact does not
  /// belong to the selected account"), so it is the one a picker has to filter
  /// on. It is also usually null: measured on the seeded org, 0 of 15 contacts
  /// had it set while 12 were in the M2M. That is why an unset value means
  /// "attaches to anyone" here rather than "belongs to nobody", and why
  /// filtering strictly on equality would empty the picker.
  final String? accountId;
  final String? accountName;

  const ContactLookup({
    required this.id,
    required this.firstName,
    required this.lastName,
    this.email,
    this.phone,
    this.accountId,
    this.accountName,
  });

  /// Whether this contact may be billed on an invoice for [forAccountId].
  ///
  /// Mirrors `InvoiceCreateSerializer.validate`, which refuses only when the
  /// contact carries a *different* account. A contact with no account passes
  /// for any of them.
  bool billableFor(String? forAccountId) =>
      accountId == null || accountId!.isEmpty || accountId == forAccountId;

  String get fullName => '$firstName $lastName'.trim();

  String get initials {
    final first = firstName.isNotEmpty ? firstName[0] : '';
    final last = lastName.isNotEmpty ? lastName[0] : '';
    return '$first$last'.toUpperCase();
  }

  factory ContactLookup.fromJson(Map<String, dynamic> json) {
    return ContactLookup(
      id: json['id']?.toString() ?? '',
      firstName: json['first_name'] as String? ?? '',
      lastName: json['last_name'] as String? ?? '',
      email: json['primary_email'] as String? ?? json['email'] as String?,
      phone: json['mobile_number'] as String? ?? json['phone'] as String?,
      // `account_detail` is the resolved FK, `{id, name}` or null. The bare
      // `account` key is read too so a leaner payload still populates this.
      accountId: json['account_detail'] is Map<String, dynamic>
          ? (json['account_detail'] as Map<String, dynamic>)['id']?.toString()
          : json['account']?.toString(),
      accountName: json['account_detail'] is Map<String, dynamic>
          ? (json['account_detail'] as Map<String, dynamic>)['name'] as String?
          : null,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ContactLookup &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// User/Profile model for assignment selector
class UserLookup {
  final String id;
  final String email;

  /// `user_details.name`, which the API has always sent and this model used to
  /// drop. Without it a picker labels somebody "aswin.1231" while the record
  /// they are assigned to labels the same person "Ashwin", from the same
  /// payload. Blank for a user who never set one.
  final String name;

  final String? profilePic;
  final String role;
  final bool isActive;

  const UserLookup({
    required this.id,
    required this.email,
    this.name = '',
    this.profilePic,
    required this.role,
    required this.isActive,
  });

  /// The name if there is one, otherwise the local part of the email.
  String get displayName =>
      name.trim().isNotEmpty ? name.trim() : email.split('@').first;

  /// Get initials for avatar
  String get initials {
    final name = displayName;
    final parts = name.split(RegExp(r'[\s._-]+'));
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name.length >= 2
        ? name.substring(0, 2).toUpperCase()
        : name.toUpperCase();
  }

  factory UserLookup.fromJson(Map<String, dynamic> json) {
    // Handle nested user_details structure from the API
    final userDetails = json['user_details'] as Map<String, dynamic>?;

    return UserLookup(
      id: json['id']?.toString() ?? '',
      email: userDetails?['email'] as String? ?? json['email'] as String? ?? '',
      name: userDetails?['name'] as String? ?? json['name'] as String? ?? '',
      profilePic:
          userDetails?['profile_pic'] as String? ??
          json['profile_pic'] as String?,
      role: json['role'] as String? ?? 'USER',
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserLookup && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Team model for selector
class TeamLookup {
  final String id;
  final String name;
  final String? description;

  const TeamLookup({required this.id, required this.name, this.description});

  factory TeamLookup.fromJson(Map<String, dynamic> json) {
    return TeamLookup(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TeamLookup && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Tag model for selector
class TagLookup {
  final String id;
  final String name;
  final String slug;
  final String color;

  const TagLookup({
    required this.id,
    required this.name,
    required this.slug,
    required this.color,
  });

  factory TagLookup.fromJson(Map<String, dynamic> json) {
    return TagLookup(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      slug: json['slug'] as String? ?? '',
      color: json['color'] as String? ?? 'gray',
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TagLookup && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// A record a task can be attached to: one id, one label, nothing else.
///
/// The task form used to source these from the leads, deals and tickets list
/// providers, which hold whatever page the corresponding screen last loaded
/// under whatever filter it last applied. On a cold app those are empty, so the
/// picker said "Nothing to pick" for an org with twenty leads.
class EntityLookup {
  final String id;
  final String label;

  const EntityLookup({required this.id, required this.label});

  /// A record with one naming field. [labelKeys] are tried in order and the
  /// first non-empty one wins.
  factory EntityLookup.fromJson(
    Map<String, dynamic> json, {
    required List<String> labelKeys,
  }) {
    return EntityLookup(
      id: json['id']?.toString() ?? '',
      label: _firstNonEmpty(json, labelKeys) ?? 'Untitled',
    );
  }

  /// A person, whose name is two optional fields rather than one. Neither is
  /// required on a lead, so [fallbackKeys] is what keeps an unnamed row
  /// selectable instead of blank.
  factory EntityLookup.person(
    Map<String, dynamic> json, {
    List<String> fallbackKeys = const [],
  }) {
    final name = [
      json['first_name']?.toString().trim() ?? '',
      json['last_name']?.toString().trim() ?? '',
    ].where((part) => part.isNotEmpty).join(' ');
    return EntityLookup(
      id: json['id']?.toString() ?? '',
      label: name.isNotEmpty
          ? name
          : (_firstNonEmpty(json, fallbackKeys) ?? 'Unnamed'),
    );
  }

  static String? _firstNonEmpty(Map<String, dynamic> json, List<String> keys) {
    for (final key in keys) {
      final value = json[key]?.toString().trim() ?? '';
      if (value.isNotEmpty) return value;
    }
    return null;
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is EntityLookup &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}
