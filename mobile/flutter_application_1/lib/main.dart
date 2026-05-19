import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import 'app.dart';

List<CameraDescription> appCameras = [];

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    appCameras = await availableCameras();
  } catch (_) {
    appCameras = [];
  }

  runApp(const MyApp());
}
