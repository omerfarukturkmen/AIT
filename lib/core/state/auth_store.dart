import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../models/auth_session_model.dart';
import '../services/auth_service.dart';
import 'analysis_history_store.dart';

class AuthStore {
  static const String _tokenKey = 'auth_access_token';
  static const String _userKey = 'auth_user';

  /// Keychain (iOS/macOS), Keystore-backed encryption (Android) and
  /// WebCrypto-encrypted storage (web).
  static const FlutterSecureStorage _storage = FlutterSecureStorage();

  static final ValueNotifier<AuthSession?> session = ValueNotifier(null);

  static bool get isSignedIn => session.value != null;

  /// Loads a remembered session and re-validates it with the backend.
  /// If the backend is unreachable the stored session is kept.
  static Future<void> restore() async {
    await _removeLegacyPlaintextSession();

    final String? token;
    final String? userJson;
    try {
      token = await _storage.read(key: _tokenKey);
      userJson = await _storage.read(key: _userKey);
    } catch (error) {
      // Unreadable storage (e.g. Keystore reset) must not block app start;
      // the user simply signs in again.
      debugPrint('AuthStore: secure storage okunamadı ($error)');
      await _clearStorage();
      return;
    }
    if (token == null || userJson == null) return;

    var user = AuthUser.fromJson(jsonDecode(userJson) as Map<String, dynamic>);
    try {
      final freshUser = await AuthService.fetchCurrentUser(token);
      if (freshUser == null) {
        await signOut();
        return;
      }
      user = freshUser;
    } on AuthException {
      // Offline: keep the remembered session.
    }
    session.value = AuthSession(accessToken: token, user: user);
  }

  /// When [remember] is false the session lives only in memory and ends
  /// when the app is closed.
  static Future<void> save(
    AuthSession newSession, {
    required bool remember,
  }) async {
    session.value = newSession;

    if (!remember) {
      await _clearStorage();
      return;
    }
    try {
      await _storage.write(key: _tokenKey, value: newSession.accessToken);
      await _storage.write(
        key: _userKey,
        value: jsonEncode(newSession.user.toJson()),
      );
    } catch (error) {
      // Sign-in still succeeds; the session just won't survive a restart.
      debugPrint('AuthStore: oturum kaydedilemedi ($error)');
    }
  }

  static Future<void> signOut() async {
    session.value = null;
    // Results are per user; don't show them to the next account.
    AnalysisHistoryStore.clearHistory();
    await _clearStorage();
  }

  static Future<void> _clearStorage() async {
    try {
      await _storage.delete(key: _tokenKey);
      await _storage.delete(key: _userKey);
    } catch (error) {
      debugPrint('AuthStore: secure storage temizlenemedi ($error)');
    }
  }

  /// Earlier builds kept the token unencrypted in shared_preferences.
  static Future<void> _removeLegacyPlaintextSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
  }
}
