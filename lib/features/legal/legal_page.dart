import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/legal_info.dart';
import '../../core/theme/app_theme.dart';
import '../../l10n/app_localizations.dart';
import '../../l10n/legal_texts.dart';
import '../../widgets/page_scaffold.dart';

enum LegalDocument { privacy, kvkk, terms }

extension LegalDocumentInfo on LegalDocument {
  String title(AppLocalizations l10n) => switch (this) {
    LegalDocument.privacy => l10n.legalPrivacyTitle,
    LegalDocument.kvkk => l10n.legalKvkkTitle,
    LegalDocument.terms => l10n.legalTermsTitle,
  };

  Map<String, List<LegalSection>> get _texts => switch (this) {
    LegalDocument.privacy => privacyPolicy,
    LegalDocument.kvkk => kvkkNotice,
    LegalDocument.terms => termsOfUse,
  };

  List<LegalSection> sections(String languageCode) =>
      _texts[languageCode] ?? _texts['tr']!;
}

class LegalPage extends StatelessWidget {
  final LegalDocument document;

  const LegalPage({super.key, required this.document});

  static Future<void> open(BuildContext context, LegalDocument document) {
    return Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => LegalPage(document: document)));
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final sections = document.sections(
      Localizations.localeOf(context).languageCode,
    );

    return Scaffold(
      appBar: AppBar(title: Text(document.title(l10n))),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            Gap.page,
            Gap.sm,
            Gap.page,
            Gap.xxl,
          ),
          children: [
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: PageScaffold.maxContentWidth,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.legalLastUpdated(LegalInfo.lastUpdated),
                      style: context.text.bodySmall,
                    ),
                    for (final (heading, body) in sections) ...[
                      const SizedBox(height: Gap.xl),
                      Semantics(
                        header: true,
                        child: Text(heading, style: context.text.titleMedium),
                      ),
                      const SizedBox(height: Gap.sm),
                      Text(
                        body,
                        style: context.text.bodyMedium?.copyWith(
                          color: context.tokens.textSecondary,
                          height: 1.6,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
