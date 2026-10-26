import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'auth_store.dart';

/// Per-user local storage, so two accounts on one device never share data.
class UserStorage {
  static String _key(String name) {
    final userId = AuthStore.session.value?.user.id;
    return 'user.${userId ?? 'anonymous'}.$name';
  }

  static Future<Object?> readJson(String name) async {
    final raw = (await SharedPreferences.getInstance()).getString(_key(name));
    if (raw == null) return null;
    try {
      return jsonDecode(raw);
    } on FormatException {
      return null;
    }
  }

  static Future<void> writeJson(String name, Object value) async {
    await (await SharedPreferences.getInstance()).setString(
      _key(name),
      jsonEncode(value),
    );
  }

  /// Removes everything stored for the current user (account deletion).
  static Future<void> clearCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final prefix = _key('');
    for (final key in prefs.getKeys().where((k) => k.startsWith(prefix))) {
      await prefs.remove(key);
    }
  }
}
