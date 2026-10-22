import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../models/auth_session_model.dart';
import '../api_config.dart';

class AuthException implements Exception {
  final String message;

  const AuthException(this.message);

  @override
  String toString() => message;
}

enum SocialAuthProvider { google, apple }

extension SocialAuthProviderLabel on SocialAuthProvider {
  String get label => switch (this) {
    SocialAuthProvider.google => 'Google',
    SocialAuthProvider.apple => 'Apple',
  };
}

/// Talks to the FastAPI `/auth` endpoints. Request bodies contain the
/// password, so they must never be logged.
class AuthService {
  static const Duration _timeout = Duration(seconds: 15);

  /// [rememberMe] false asks the backend for a short (12 hour) session.
  static Future<AuthSession> login({
    required String email,
    required String password,
    bool rememberMe = true,
  }) async {
    final data = await _post('/auth/login', {
      'email': email.trim(),
      'password': password,
      'remember_me': rememberMe,
    });
    return AuthSession.fromJson(data);
  }

  /// Revokes the token on the server. Best effort: signing out locally must
  /// work offline too, so failures are ignored.
  static Future<void> logout(String accessToken) async {
    try {
      await http
          .post(
            Uri.parse('${ApiConfig.baseUrl}/auth/logout'),
            headers: {'Authorization': 'Bearer $accessToken'},
          )
          .timeout(const Duration(seconds: 5));
    } on Exception {
      // Token expires on its own; nothing else to do.
    }
  }

  static Future<AuthSession> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    final data = await _post('/auth/register', {
      'full_name': fullName.trim(),
      'email': email.trim(),
      'password': password,
    });
    return AuthSession.fromJson(data);
  }

  /// Returns null when the token is rejected; throws [AuthException] when the
  /// server cannot be reached so callers can keep an offline session.
  static Future<AuthUser?> fetchCurrentUser(String accessToken) async {
    final http.Response response;
    try {
      response = await http
          .get(
            Uri.parse('${ApiConfig.baseUrl}/auth/me'),
            headers: {'Authorization': 'Bearer $accessToken'},
          )
          .timeout(_timeout);
    } on Exception {
      throw const AuthException('Sunucuya ulaşılamadı.');
    }

    if (response.statusCode == 401) return null;
    if (response.statusCode != 200) {
      throw AuthException(_errorMessage(response));
    }
    return AuthUser.fromJson(
      jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>,
    );
  }

  /// Permanently deletes the account with all videos and analyses (KVKK).
  static Future<void> deleteAccount(String accessToken) async {
    final http.Response response;
    try {
      response = await http
          .delete(
            Uri.parse('${ApiConfig.baseUrl}/auth/me'),
            headers: {'Authorization': 'Bearer $accessToken'},
          )
          .timeout(_timeout);
    } on Exception {
      throw const AuthException(
        'Sunucuya ulaşılamadı. Hesabın silinmedi; lütfen tekrar dene.',
      );
    }

    if (response.statusCode != 200) {
      throw AuthException(_errorMessage(response));
    }
  }

  /// Integration point for Google / Apple sign-in.
  ///
  /// GEÇİCİ: Sosyal giriş henüz yapılandırılmadı. Etkinleştirmek için:
  /// 1. `google_sign_in` ve `sign_in_with_apple` paketlerini ekleyin ve
  ///    platform yapılandırmalarını yapın (README'deki "Kimlik doğrulama"
  ///    bölümüne bakın).
  /// 2. Backend'e sağlayıcıdan gelen ID token'ı doğrulayan
  ///    `/auth/google` ve `/auth/apple` uçlarını ekleyin.
  /// 3. Bu metodu ID token'ı backend'e gönderip [AuthSession] dönecek
  ///    şekilde güncelleyin.
  static Future<AuthSession> signInWithProvider(
    SocialAuthProvider provider,
  ) async {
    throw AuthException(
      '${provider.label} ile giriş henüz yapılandırılmadı. '
      'Şimdilik e-posta ve şifre ile devam edebilirsin.',
    );
  }

  static Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    final http.Response response;
    try {
      response = await http
          .post(
            Uri.parse('${ApiConfig.baseUrl}$path'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(_timeout);
    } on TimeoutException {
      throw const AuthException(
        'Sunucu yanıt vermedi. Lütfen biraz sonra tekrar dene.',
      );
    } on Exception {
      throw const AuthException(
        'Sunucuya ulaşılamadı. İnternet bağlantını ve backend\'in '
        'çalıştığını kontrol et.',
      );
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AuthException(_errorMessage(response));
    }
    return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
  }

  static String _errorMessage(http.Response response) {
    try {
      final detail =
          (jsonDecode(utf8.decode(response.bodyBytes)) as Map)['detail'];
      if (detail is String && detail.isNotEmpty) return detail;
    } on Exception {
      // Fall through to the generic message below.
    }
    if (response.statusCode >= 500) {
      return 'Sunucuda bir hata oluştu. Lütfen tekrar dene.';
    }
    return 'İşlem tamamlanamadı (hata kodu ${response.statusCode}).';
  }
}
