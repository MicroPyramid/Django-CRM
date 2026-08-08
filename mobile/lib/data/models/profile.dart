import 'auth_response.dart';

/// User's profile within the current organization.
///
/// Returned by GET /api/auth/profile/ (ProfileDetailSerializer).
/// The mobile app can only PATCH the `phone` field via /api/profile/.
/// Other fields are display-only by API contract.
class Profile {
  final String id;
  final AuthUser user;
  final Organization? org;
  final String? role;
  final bool isOrganizationAdmin;
  final bool hasSalesAccess;
  final bool hasMarketingAccess;
  final String? phone;
  final DateTime? dateOfJoining;
  final bool isActive;

  /// The teams you are on, by name. Only ever your own: the endpoint
  /// serializes `request.profile` and takes no id.
  final List<String> teams;

  /// When you last signed in. Null on a profile that never has, and on any
  /// payload from a build older than this field.
  final DateTime? lastLogin;

  const Profile({
    required this.id,
    required this.user,
    this.org,
    this.role,
    this.isOrganizationAdmin = false,
    this.hasSalesAccess = false,
    this.hasMarketingAccess = false,
    this.phone,
    this.dateOfJoining,
    this.isActive = true,
    this.teams = const [],
    this.lastLogin,
  });

  factory Profile.fromJson(Map<String, dynamic> json) {
    return Profile(
      id: json['id'] as String,
      user: AuthUser.fromJson(json['user'] as Map<String, dynamic>),
      org: json['org'] is Map<String, dynamic>
          ? Organization.fromJson(json['org'] as Map<String, dynamic>)
          : null,
      role: json['role'] as String?,
      isOrganizationAdmin: json['is_organization_admin'] as bool? ?? false,
      hasSalesAccess: json['has_sales_access'] as bool? ?? false,
      hasMarketingAccess: json['has_marketing_access'] as bool? ?? false,
      phone: json['phone'] as String?,
      dateOfJoining: json['date_of_joining'] != null
          ? DateTime.tryParse(json['date_of_joining'] as String)
          : null,
      isActive: json['is_active'] as bool? ?? true,
      teams:
          (json['teams'] as List?)?.map((t) => t.toString()).toList() ??
          const [],
      lastLogin: json['last_login'] != null
          ? DateTime.tryParse(json['last_login'] as String)
          : null,
    );
  }

  Profile copyWith({String? phone}) {
    return Profile(
      id: id,
      user: user,
      org: org,
      role: role,
      isOrganizationAdmin: isOrganizationAdmin,
      hasSalesAccess: hasSalesAccess,
      hasMarketingAccess: hasMarketingAccess,
      phone: phone ?? this.phone,
      dateOfJoining: dateOfJoining,
      isActive: isActive,
      teams: teams,
      lastLogin: lastLogin,
    );
  }
}
