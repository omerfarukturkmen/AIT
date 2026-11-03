import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../models/auth_session_model.dart';
import '../api_config.dart';
import '../app_exception.dart';

/// Talks to the FastAPI `/auth` endpoints. Request bodies can contain the
/// password, so they must never be logged.
class AuthService {
  static const Duration _timeout = Duration(seconds: 15);

  static Uri _uri(String path) => Uri.parse('${ApiConfig.baseUrl}$path');

  static Map<String, String> _headers([String? token]) => {
    'Content-Type': 'application/json',
    if (token != null) 'Authorization': 'Bearer $token',
  };

  /// [rememberMe] false asks the backend for a short (12 hour) session.
  static Future<AuthSession> login({
    required String email,
    required String password,
    bool rememberMe = true,
  }) async {
    final data = await _request(
      'POST',
      '/auth/login',
      body: {
        'email': email.trim(),
        'password': password,
        'remember_me': rememberMe,
      },
      unauthorizedKind: ErrorKind.invalidCredentials,
    );
    return AuthSession.fromJson(data);
  }

  static Future<AuthSession> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    final data = await _request(
      'POST',
      '/auth/register',
      body: {
        'full_name': fullName.trim(),
        'email': email.trim(),
        'password': password,
      },
    );
    return AuthSession.fromJson(data);
  }

  /// Exchanges a Google or Apple ID token for an AIT session.
  static Future<AuthSession> socialSignIn({
    required String provider,
    required String idToken,
    String? fullName,
  }) async {
    final data = await _request(
      'POST',
      '/auth/$provider',
      body: provider == 'apple'
          ? {'identity_token': idToken, 'full_name': ?fullName}
          : {'id_token': idToken},
    );
    return AuthSession.fromJson(data);
  }

  /// Returns null when the token is rejected; throws [AppException] when the
  /// server cannot be reached so callers can keep an offline session.
  static Future<AuthUser?> fetchCurrentUser(String accessToken) async {
    try {
      final data = await _request('GET', '/auth/me', token: accessToken);
      return AuthUser.fromJson(data);
    } on AppException catch (error) {
      if (error.kind == ErrorKind.unauthorized) return null;
      rethrow;
    }
  }

  static Future<void> requestPasswordReset(String email) => _request(
    'POST',
    '/auth/password-reset/request',
    body: {'email': email.trim()},
  );

  static Future<void> confirmPasswordReset({
    required String email,
    required String code,
    required String newPassword,
  }) => _request(
    'POST',
    '/auth/password-reset/confirm',
    body: {
      'email': email.trim(),
      'code': code.trim(),
      'new_password': newPassword,
    },
    badRequestKind: ErrorKind.invalidCode,
  );

  static Future<void> requestEmailVerification(String accessToken) =>
      _request('POST', '/auth/email-verification/request', token: accessToken);

  static Future<void> confirmEmailVerification(
    String accessToken,
    String code,
  ) => _request(
    'POST',
    '/auth/email-verification/confirm',
    token: accessToken,
    body: {'code': code.trim()},
    badRequestKind: ErrorKind.invalidCode,
  );

  /// Revokes the token on the server. Best effort: signing out locally must
  /// work offline too, so failures are ignored.
  static Future<void> logout(
    String accessToken, {
    bool allDevices = false,
  }) async {
    try {
      await http
          .post(
            _uri('/auth/logout${allDevices ? '?all_devices=true' : ''}'),
            headers: _headers(accessToken),
          )
          .timeout(const Duration(seconds: 5));
    } on Exception {
      // The token expires on its own; nothing else to do.
    }
  }

  /// Permanently deletes the account with all videos and analyses (KVKK).
  static Future<void> deleteAccount(String accessToken) =>
      _request('DELETE', '/auth/me', token: accessToken);

  static Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
    String? token,
    ErrorKind unauthorizedKind = ErrorKind.unauthorized,
    ErrorKind badRequestKind = ErrorKind.invalidInput,
  }) async {
    final http.Response response;
    final client = http.Client();
    try {
      final request = http.Request(method, _uri(path))
        ..headers.addAll(_headers(token));
      if (body != null) request.body = jsonEncode(body);
      response = await http.Response.fromStream(
        await client.send(request).timeout(_timeout),
      ).timeout(_timeout);
    } on TimeoutException {
      throw const AppException(ErrorKind.timeout);
    } on Exception {
      throw const AppException(ErrorKind.network);
    } finally {
      client.close();
    }

    Map<String, dynamic> json = const {};
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map<String, dynamic>) json = decoded;
    } on FormatException {
      // Empty or non-JSON body.
    }

    final status = response.statusCode;
    if (status >= 200 && status < 300) return json;

    final detail = json['detail'] is String ? json['detail'] as String : null;
    throw switch (status) {
      401 => AppException(unauthorizedKind, detail),
      400 => AppException(badRequestKind, detail),
      _ => AppException.fromStatus(status, detail),
    };
  }
}
