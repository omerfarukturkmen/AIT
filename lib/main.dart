import 'package:flutter/material.dart';

import 'app.dart';
import 'core/state/app_settings_store.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Theme and language must be known before the first frame.
  await AppSettingsStore.load();
  runApp(const MyApp());
}
