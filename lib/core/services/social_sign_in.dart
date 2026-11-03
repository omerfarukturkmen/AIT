import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';

import '../../models/auth_session_model.dart';
import '../app_exception.dart';
import 'auth_service.dart';

enum SocialProvider { google, apple }

/// Build-time configuration (see docs/SOSYAL_GIRIS_KURULUMU.md):
/// `--dart-define=GOOGLE_SERVER_CLIENT_ID=...` (web OAuth client id),
/// `--dart-define=GOOGLE_IOS_CLIENT_ID=...` (iOS OAuth client id),
/// `--dart-define=APPLE_SIGN_IN_ENABLED=true`.
abstract final class SocialSignInConfig {
  static const googleServerClientId = String.fromEnvironment(
    'GOOGLE_SERVER_CLIENT_ID',
  );
  static const googleIosClientId = String.fromEnvironment(
    'GOOGLE_IOS_CLIENT_ID',
  );
  static const appleEnabled = bool.fromEnvironment('APPLE_SIGN_IN_ENABLED');
}

class SocialSignIn {
  static bool _googleInitialized = false;

  static bool get _isApplePlatform =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.iOS ||
          defaultTargetPlatform == TargetPlatform.macOS);

  static bool get _isMobile =>
      !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.android ||
          defaultTargetPlatform == TargetPlatform.iOS);

  /// True when the provider is configured and works on this platform.
  /// (Google on web needs Google's own rendered button; not set up yet.)
  static bool isAvailable(SocialProvider provider) => switch (provider) {
    SocialProvider.google =>
      _isMobile && SocialSignInConfig.googleServerClientId.isNotEmpty,
    SocialProvider.apple => _isApplePlatform && SocialSignInConfig.appleEnabled,
  };

  /// Signs in with the provider and exchanges its ID token for an AIT
  /// session. Returns null if the user cancelled.
  static Future<AuthSession?> signIn(SocialProvider provider) async {
    if (!isAvailable(provider)) {
      throw const AppException(ErrorKind.notConfigured);
    }
    return switch (provider) {
      SocialProvider.google => _google(),
      SocialProvider.apple => _apple(),
    };
  }

  static Future<AuthSession?> _google() async {
    final google = GoogleSignIn.instance;
    try {
      if (!_googleInitialized) {
        await google.initialize(
          clientId: SocialSignInConfig.googleIosClientId.isEmpty
              ? null
              : SocialSignInConfig.googleIosClientId,
          serverClientId: SocialSignInConfig.googleServerClientId,
        );
        _googleInitialized = true;
      }
      final account = await google.authenticate();
      final idToken = account.authentication.idToken;
      if (idToken == null) throw const AppException(ErrorKind.unknown);
      return AuthService.socialSignIn(provider: 'google', idToken: idToken);
    } on GoogleSignInException catch (error) {
      if (error.code == GoogleSignInExceptionCode.canceled) return null;
      throw const AppException(ErrorKind.unknown);
    }
  }

  static Future<AuthSession?> _apple() async {
    try {
      final credential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );
      final token = credential.identityToken;
      if (token == null) throw const AppException(ErrorKind.unknown);
      final name = [
        credential.givenName,
        credential.familyName,
      ].whereType<String>().where((part) => part.trim().isNotEmpty).join(' ');
      return AuthService.socialSignIn(
        provider: 'apple',
        idToken: token,
        fullName: name.isEmpty ? null : name,
      );
    } on SignInWithAppleAuthorizationException catch (error) {
      if (error.code == AuthorizationErrorCode.canceled) return null;
      throw const AppException(ErrorKind.unknown);
    }
  }
}
