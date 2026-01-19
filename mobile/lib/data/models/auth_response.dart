/// User returned from authentication endpoints
class AuthUser {
  final String id;
  final String email;
  final String? name;
  final String? profilePic;

  const AuthUser({
    required this.id,
    required this.email,
    this.name,
    this.profilePic,
  });

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id'] as String,
      email: json['email'] as String,
      name: json['name'] as String?,
      profilePic: json['profile_pic'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'profile_pic': profilePic,
    };
  }

  /// Get display name (email if name not available)
  String get displayName => name ?? email.split('@').first;

  /// Get initials for avatar fallback
  String get initials {
    final parts = displayName.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return displayName.substring(0, displayName.length >= 2 ? 2 : 1).toUpperCase();
  }

  @override
  String toString() => 'AuthUser(id: $id, email: $email)';
}

/// Organization model for multi-tenancy
class Organization {
  final String id;
  final String name;
  final String? role;
  final String? defaultCurrency;
  final String? currencySymbol;
  final String? defaultCountry;

  const Organization({
    required this.id,
    required this.name,
    this.role,
    this.defaultCurrency,
    this.currencySymbol,
    this.defaultCountry,
  });

  factory Organization.fromJson(Map<String, dynamic> json) {
    return Organization(
      id: json['id'] as String,
      name: json['name'] as String,
      role: json['role'] as String?,
      defaultCurrency: json['default_currency'] as String?,
      currencySymbol: json['currency_symbol'] as String?,
      defaultCountry: json['default_country'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'role': role,
      'default_currency': defaultCurrency,
      'currency_symbol': currencySymbol,
      'default_country': defaultCountry,
    };
  }

  /// Get initials for avatar fallback
  String get initials {
    if (name.isEmpty) return 'O';
    final parts = name.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name.substring(0, name.length >= 2 ? 2 : 1).toUpperCase();
  }

  @override
  String toString() => 'Organization(id: $id, name: $name, role: $role)';
}

/// Response from Google OAuth callback
class AuthResponse {
  final String accessToken;
  final String refreshToken;
  final AuthUser user;

  const AuthResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      user: AuthUser.fromJson(json['user'] as Map<String, dynamic>),
    );
  }

  @override
  String toString() => 'AuthResponse(user: ${user.email})';
}

/// Response from login endpoint (includes organizations)
class LoginResponse {
  final String accessToken;
  final String refreshToken;
  final AuthUser user;
  final List<Organization> organizations;
  final Organization? currentOrg;

  const LoginResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
    required this.organizations,
    this.currentOrg,
  });

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      user: AuthUser.fromJson(json['user'] as Map<String, dynamic>),
      organizations: (json['user']['organizations'] as List<dynamic>?)
              ?.map((org) => Organization.fromJson(org as Map<String, dynamic>))
              .toList() ??
          [],
      currentOrg: json['current_org'] != null
          ? Organization.fromJson(json['current_org'] as Map<String, dynamic>)
          : null,
    );
  }

  @override
  String toString() => 'LoginResponse(user: ${user.email}, orgs: ${organizations.length})';
}
