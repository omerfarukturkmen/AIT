import 'package:flutter/material.dart';

class Achievement {
  final String title;
  final IconData icon;
  final bool isUnlocked;

  const Achievement({
    required this.title,
    required this.icon,
    required this.isUnlocked,
  });
}
