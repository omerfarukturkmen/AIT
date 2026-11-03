import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_application_1/core/state/auth_store.dart';
import 'package:flutter_application_1/features/auth/auth_page.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'helpers.dart';

Map<String, dynamic> _sessionJson(String fullName) => {
  'access_token': 'test-token',
  'token_type': 'bearer',
  'user': {'id': 1, 'email': 'ayse@example.com', 'full_name': fullName},
};

Future<void> _pumpAuthPage(
  WidgetTester tester, {
  Size size = const Size(420, 1100),
  bool dark = false,
  WidgetBuilder? homeBuilder,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    wrapApp(
      AuthPage(homeBuilder: homeBuilder),
      themeMode: dark ? ThemeMode.dark : ThemeMode.light,
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _tapVisible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
    AuthStore.session.value = null;
  });

  testWidgets('login shows validation errors for empty fields', (tester) async {
    await _pumpAuthPage(tester);

    expect(find.text('Tekrar hoş geldin'), findsOneWidget);
    expect(find.text('Google ile devam et'), findsOneWidget);
    expect(find.text('Apple ile devam et'), findsOneWidget);
    expect(find.text('veya'), findsOneWidget);

    await _tapVisible(tester, find.byKey(const Key('login_submit')));

    expect(find.text('E-posta adresi gerekli.'), findsOneWidget);
    expect(find.text('Şifre gerekli.'), findsOneWidget);
  });

  testWidgets('password visibility toggle works', (tester) async {
    await _pumpAuthPage(tester);

    EditableText passwordField() => tester.widget<EditableText>(
      find.descendant(
        of: find.byKey(const Key('login_password')),
        matching: find.byType(EditableText),
      ),
    );

    expect(passwordField().obscureText, isTrue);
    await tester.tap(find.byTooltip('Şifreyi göster'));
    await tester.pump();
    expect(passwordField().obscureText, isFalse);
    await tester.tap(find.byTooltip('Şifreyi gizle'));
    await tester.pump();
    expect(passwordField().obscureText, isTrue);
  });

  testWidgets('switches between login and register', (tester) async {
    await _pumpAuthPage(tester);

    await _tapVisible(tester, find.text('Kayıt ol'));
    expect(find.text('Hesabını oluştur'), findsOneWidget);
    expect(find.text('Google ile kayıt ol'), findsOneWidget);
    expect(find.text('Apple ile kayıt ol'), findsOneWidget);

    await _tapVisible(tester, find.text('Giriş yap'));
    expect(find.text('Tekrar hoş geldin'), findsOneWidget);
  });

  testWidgets('register validates passwords, match and terms', (tester) async {
    await _pumpAuthPage(tester);
    await _tapVisible(tester, find.text('Kayıt ol'));

    await tester.enterText(
      find.byKey(const Key('register_name')),
      'Ayşe Yılmaz',
    );
    await tester.enterText(
      find.byKey(const Key('register_email')),
      'ayse@example',
    );
    await tester.enterText(find.byKey(const Key('register_password')), 'kisa');
    await tester.enterText(find.byKey(const Key('register_confirm')), 'farkli');
    await _tapVisible(tester, find.byKey(const Key('register_submit')));

    expect(find.textContaining('Geçerli bir e-posta'), findsOneWidget);
    expect(find.text('Şifre en az 8 karakter olmalı.'), findsOneWidget);
    expect(find.text('Şifreler eşleşmiyor.'), findsOneWidget);
    expect(
      find.text('Devam etmek için koşulları kabul etmelisin.'),
      findsOneWidget,
    );
  });

  testWidgets('social buttons explain they are not configured', (tester) async {
    await _pumpAuthPage(tester);

    await _tapVisible(tester, find.text('Google ile devam et'));

    expect(
      find.textContaining('Google ile giriş bu cihazda henüz kullanılamıyor'),
      findsOneWidget,
    );
    expect(AuthStore.session.value, isNull);
  });

  testWidgets('login shows server error message', (tester) async {
    await http.runWithClient(
      () async {
        await _pumpAuthPage(tester);

        await tester.enterText(
          find.byKey(const Key('login_email')),
          'ayse@example.com',
        );
        await tester.enterText(
          find.byKey(const Key('login_password')),
          'yanlis1234',
        );
        await _tapVisible(tester, find.byKey(const Key('login_submit')));

        expect(find.text('E-posta veya şifre hatalı.'), findsOneWidget);
        expect(AuthStore.session.value, isNull);
      },
      () => MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'E-posta veya şifre hatalı.'}),
          401,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );
  });

  testWidgets('successful register stores session and opens the app', (
    tester,
  ) async {
    late Map<String, dynamic> sentBody;

    await http.runWithClient(
      () async {
        await _pumpAuthPage(
          tester,
          homeBuilder: (_) => const Scaffold(body: Text('home')),
        );
        await _tapVisible(tester, find.text('Kayıt ol'));

        await tester.enterText(
          find.byKey(const Key('register_name')),
          'Ayşe Yılmaz',
        );
        await tester.enterText(
          find.byKey(const Key('register_email')),
          'ayse@example.com',
        );
        await tester.enterText(
          find.byKey(const Key('register_password')),
          'guclu1234',
        );
        await tester.enterText(
          find.byKey(const Key('register_confirm')),
          'guclu1234',
        );
        await _tapVisible(tester, find.byKey(const Key('register_terms')));
        await tester.ensureVisible(find.byKey(const Key('register_submit')));
        await tester.tap(find.byKey(const Key('register_submit')));
        // Let the request complete without settling MainNavigationPage's
        // ongoing animations.
        for (var i = 0; i < 10; i++) {
          await tester.pump(const Duration(milliseconds: 100));
        }
      },
      () => MockClient((request) async {
        if (request.url.path == '/analyses') {
          return http.Response('{"analyses": []}', 200);
        }
        sentBody = jsonDecode(request.body) as Map<String, dynamic>;
        return http.Response(
          jsonEncode(_sessionJson('Ayşe Yılmaz')),
          201,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );

    expect(sentBody['email'], 'ayse@example.com');
    expect(sentBody['full_name'], 'Ayşe Yılmaz');
    expect(AuthStore.session.value?.user.fullName, 'Ayşe Yılmaz');
    expect(find.text('home'), findsOneWidget);
    expect(find.textContaining('Hesabın oluşturuldu'), findsOneWidget);
  });

  for (final (name, size, dark) in [
    ('phone', const Size(360, 780), false),
    ('tablet', const Size(820, 1180), true),
    ('desktop', const Size(1440, 900), false),
  ]) {
    testWidgets('lays out without overflow on $name', (tester) async {
      await _pumpAuthPage(tester, size: size, dark: dark);
      expect(tester.takeException(), isNull);

      await _tapVisible(tester, find.text('Kayıt ol'));
      expect(tester.takeException(), isNull);
    });
  }
}
