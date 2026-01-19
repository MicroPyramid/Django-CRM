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

  const ContactLookup({
    required this.id,
    required this.firstName,
    required this.lastName,
    this.email,
    this.phone,
  });

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
  final String? profilePic;
  final String role;
  final bool isActive;

  const UserLookup({
    required this.id,
    required this.email,
    this.profilePic,
    required this.role,
    required this.isActive,
  });

  /// Get display name from email (part before @)
  String get displayName => email.split('@').first;

  /// Get initials for avatar
  String get initials {
    final name = displayName;
    final parts = name.split(RegExp(r'[._-]'));
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name.length >= 2 ? name.substring(0, 2).toUpperCase() : name.toUpperCase();
  }

  factory UserLookup.fromJson(Map<String, dynamic> json) {
    // Handle nested user_details structure from the API
    final userDetails = json['user_details'] as Map<String, dynamic>?;

    return UserLookup(
      id: json['id']?.toString() ?? '',
      email: userDetails?['email'] as String? ?? json['email'] as String? ?? '',
      profilePic: userDetails?['profile_pic'] as String? ?? json['profile_pic'] as String?,
      role: json['role'] as String? ?? 'USER',
      isActive: json['is_active'] as bool? ?? true,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserLookup &&
          runtimeType == other.runtimeType &&
          id == other.id;

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
      other is TagLookup &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}
