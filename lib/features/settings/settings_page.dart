import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';
import '../../../core/state/app_settings_store.dart';
import '../../../widgets/glass_card.dart';
import '../../../widgets/premium_background.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  Color _mainTextColor(AppSettings settings) {
    return settings.isDarkMode ? AppColors.text : const Color(0xFF0F172A);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PremiumBackground(
        child: SafeArea(
          child: ValueListenableBuilder<AppSettings>(
            valueListenable: AppSettingsStore.settings,
            builder: (context, settings, child) {
              return SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      'Ayarlar',
                      style: TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w900,
                        color: _mainTextColor(settings),
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Uygulama deneyimini, sesli geri bildirimleri, tema görünümünü ve demo modunu buradan yönetebilirsin.',
                      style: TextStyle(color: AppColors.textSoft, height: 1.4),
                    ),
                    const SizedBox(height: 22),
                    _AppearanceSettingsCard(settings: settings),
                    const SizedBox(height: 16),
                    _VoiceSettingsCard(settings: settings),
                    const SizedBox(height: 16),
                    _SystemStatusCard(settings: settings),
                    const SizedBox(height: 16),
                    const _AppInfoCard(),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _AppearanceSettingsCard extends StatelessWidget {
  final AppSettings settings;

  const _AppearanceSettingsCard({required this.settings});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _CardTitle(icon: Icons.palette_rounded, title: 'Görünüm'),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _ThemeOptionCard(
                  title: 'Dark Mode',
                  subtitle: 'Neon fitness dashboard',
                  icon: Icons.dark_mode_rounded,
                  isSelected: settings.isDarkMode,
                  onTap: () {
                    AppSettingsStore.updateThemeMode(true);
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _ThemeOptionCard(
                  title: 'Light Mode',
                  subtitle: 'Temiz beyaz görünüm',
                  icon: Icons.light_mode_rounded,
                  isSelected: !settings.isDarkMode,
                  onTap: () {
                    AppSettingsStore.updateThemeMode(false);
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ThemeOptionCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _ThemeOptionCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = isSelected ? AppColors.primary : AppColors.textSoft;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withValues(alpha: isSelected ? 0.16 : 0.06),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: color.withValues(alpha: isSelected ? 0.42 : 0.14),
          ),
          boxShadow: [
            if (isSelected)
              BoxShadow(
                color: color.withValues(alpha: 0.18),
                blurRadius: 24,
                offset: const Offset(0, 10),
              ),
          ],
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 30),
            const SizedBox(height: 10),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w900,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.textSoft,
                fontSize: 11,
                height: 1.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VoiceSettingsCard extends StatelessWidget {
  final AppSettings settings;

  const _VoiceSettingsCard({required this.settings});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _CardTitle(
            icon: Icons.volume_up_rounded,
            title: 'Sesli Geri Bildirim',
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Egzersiz sırasında sesli uyarı al',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
              Switch(
                value: settings.voiceFeedbackEnabled,
                activeThumbColor: AppColors.purpleGlow,
                activeTrackColor: AppColors.purpleGlow.withValues(alpha: 0.35),
                onChanged: AppSettingsStore.updateVoiceFeedback,
              ),
            ],
          ),
          const SizedBox(height: 12),
          _SettingsDropdown<String>(
            icon: Icons.language_rounded,
            title: 'Dil',
            value: settings.languageCode,
            items: const [
              DropdownMenuItem(value: 'tr-TR', child: Text('Türkçe')),
              DropdownMenuItem(value: 'en-US', child: Text('English')),
            ],
            onChanged: (value) {
              if (value != null) {
                AppSettingsStore.updateLanguage(value);
              }
            },
          ),
          const SizedBox(height: 12),
          _SettingsDropdown<int>(
            icon: Icons.timer_rounded,
            title: 'Uyarı Sıklığı',
            value: settings.feedbackIntervalSeconds,
            items: const [
              DropdownMenuItem(value: 2, child: Text('2 saniye')),
              DropdownMenuItem(value: 5, child: Text('5 saniye')),
              DropdownMenuItem(value: 10, child: Text('10 saniye')),
            ],
            onChanged: (value) {
              if (value != null) {
                AppSettingsStore.updateFeedbackInterval(value);
              }
            },
          ),
        ],
      ),
    );
  }
}

class _SystemStatusCard extends StatelessWidget {
  final AppSettings settings;

  const _SystemStatusCard({required this.settings});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _CardTitle(
            icon: Icons.cloud_sync_rounded,
            title: 'Sistem Durumu',
          ),
          const SizedBox(height: 14),
          _StatusRow(
            title: 'Demo Mode',
            subtitle: settings.demoModeEnabled
                ? 'Fake AI service aktif'
                : 'Demo mode kapalı',
            value: settings.demoModeEnabled,
            activeColor: Colors.greenAccent,
          ),
          const SizedBox(height: 12),
          _StatusRow(
            title: 'Backend API',
            subtitle: settings.backendReady
                ? 'Backend bağlantısı hazır'
                : 'Backend API bekleniyor',
            value: settings.backendReady,
            activeColor: AppColors.purpleGlow,
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.purpleGlow.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(
                color: AppColors.purpleGlow.withValues(alpha: 0.22),
              ),
            ),
            child: const Text(
              'Backend endpoint geldiğinde sadece service katmanı güncellenecek. UI, model ve sonuç ekranı aynı yapıyla çalışmaya devam edecek.',
              style: TextStyle(
                color: AppColors.textSoft,
                height: 1.45,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool value;
  final Color activeColor;

  const _StatusRow({
    required this.title,
    required this.subtitle,
    required this.value,
    required this.activeColor,
  });

  @override
  Widget build(BuildContext context) {
    final statusColor = value ? activeColor : Colors.orangeAccent;

    return Row(
      children: [
        Container(
          height: 42,
          width: 42,
          decoration: BoxDecoration(
            color: statusColor.withValues(alpha: 0.13),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: statusColor.withValues(alpha: 0.25)),
          ),
          child: Icon(
            value ? Icons.check_circle_rounded : Icons.pending_rounded,
            color: statusColor,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w900,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: const TextStyle(color: AppColors.textSoft, fontSize: 12),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _AppInfoCard extends StatelessWidget {
  const _AppInfoCard();

  @override
  Widget build(BuildContext context) {
    return const GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _CardTitle(
            icon: Icons.info_outline_rounded,
            title: 'Uygulama Bilgisi',
          ),
          SizedBox(height: 14),
          _InfoLine(title: 'Uygulama', value: 'AIT Fitness Trainer'),
          _InfoLine(title: 'Frontend', value: 'Flutter'),
          _InfoLine(title: 'Analiz Modu', value: 'Live Camera + Upload Video'),
          _InfoLine(title: 'AI Durumu', value: 'Demo Service / API Ready'),
          _InfoLine(title: 'Versiyon', value: '1.0.0'),
        ],
      ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  final String title;
  final String value;

  const _InfoLine({required this.title, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 11),
      child: Row(
        children: [
          Expanded(
            child: Text(
              title,
              style: const TextStyle(color: AppColors.textSoft),
            ),
          ),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}

class _SettingsDropdown<T> extends StatelessWidget {
  final IconData icon;
  final String title;
  final T value;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?> onChanged;

  const _SettingsDropdown({
    required this.icon,
    required this.title,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.10)),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.purpleGlow, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
          DropdownButton<T>(
            value: value,
            items: items,
            onChanged: onChanged,
            underline: const SizedBox(),
            dropdownColor: AppColors.bg2,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
            ),
            iconEnabledColor: AppColors.purpleGlow,
          ),
        ],
      ),
    );
  }
}

class _CardTitle extends StatelessWidget {
  final IconData icon;
  final String title;

  const _CardTitle({required this.icon, required this.title});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: AppColors.purpleGlow),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            title,
            style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900),
          ),
        ),
      ],
    );
  }
}
