class AuthUser {
  final int id;
  final String email;
  final String fullName;
  final bool emailVerified;

  const AuthUser({
    required this.id,
    required this.email,
    required this.fullName,
    this.emailVerified = false,
  });

  String get firstName => fullName.trim().split(RegExp(r'\s+')).first;

  /// Up to two initials for the avatar.
  String get initials {
    final parts = fullName
        .trim()
        .split(RegExp(r'\s+'))
        .where((p) => p.isNotEmpty);
    final letters = parts.take(2).map((p) => p.characters.first.toUpperCase());
    return letters.isEmpty ? '?' : letters.join();
  }

  AuthUser copyWith({bool? emailVerified}) => AuthUser(
    id: id,
    email: email,
    fullName: fullName,
    emailVerified: emailVerified ?? this.emailVerified,
  );

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id'] as int,
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      emailVerified: json['email_verified'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'full_name': fullName,
    'email_verified': emailVerified,
  };
}

class AuthSession {
  final String accessToken;
  final AuthUser user;

  const AuthSession({required this.accessToken, required this.user});

  AuthSession copyWith({AuthUser? user}) =>
      AuthSession(accessToken: accessToken, user: user ?? this.user);

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      accessToken: json['access_token'] as String,
      user: AuthUser.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}

extension on String {
  Iterable<String> get characters => runes.map(String.fromCharCode);
}
