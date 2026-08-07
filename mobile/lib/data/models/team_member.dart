/// A person in the org, as `/api/users/` returns them.
///
/// Two ids, and they are not interchangeable. `id` is the Profile row, which
/// is what `assigned_to` and every picker filters on. `userId` is the User row,
/// which is the pk `/api/user/<id>/` and `/api/user/<id>/status/` take. Mixing
/// the two has silently disabled permission checks in this codebase before, so
/// both are kept and neither is derived from the other.
class TeamMember {
  const TeamMember({
    required this.id,
    required this.userId,
    required this.name,
    required this.email,
    required this.role,
    required this.isActive,
    this.lastLogin,
    this.activeTokenCount = 0,
  });

  /// Profile id.
  final String id;

  /// User id, the one the role and status endpoints address.
  final String userId;
  final String name;
  final String email;

  /// `ADMIN` or `USER`. The server recognises no others.
  final String role;
  final bool isActive;
  final DateTime? lastLogin;

  /// API tokens still authenticating as this person. The number worth acting
  /// on when the account is deactivated: the login is gone, the token is not.
  final int activeTokenCount;

  bool get isAdmin => role == 'ADMIN';

  /// Someone invited who has not signed in yet.
  bool get hasNeverSignedIn => lastLogin == null;

  factory TeamMember.fromJson(Map<String, dynamic> json) {
    final details = (json['user_details'] as Map<String, dynamic>?) ?? const {};
    final email = (details['email'] as String?) ?? '';
    final rawLogin = details['last_login'] as String?;
    return TeamMember(
      id: (json['id'] ?? '').toString(),
      userId: (details['id'] ?? '').toString(),
      // An invited person has no name until they sign in, so the email is the
      // only thing there is to call them.
      name: (details['name'] as String?)?.trim().isNotEmpty == true
          ? (details['name'] as String).trim()
          : (email.isNotEmpty ? email : 'Unnamed'),
      email: email,
      role: (json['role'] as String?) ?? 'USER',
      isActive: json['is_active'] as bool? ?? true,
      lastLogin: rawLogin == null ? null : DateTime.tryParse(rawLogin),
      activeTokenCount: json['active_token_count'] as int? ?? 0,
    );
  }
}

/// The two roles the backend accepts. `ApprovalRule` offers a MANAGER value,
/// but `Profile.role` does not, and offering a value the server rejects is
/// worse than not offering it.
const List<String> teamRoles = ['ADMIN', 'USER'];
