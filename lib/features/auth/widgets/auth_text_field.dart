import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../app.dart';
import '../../../core/theme/app_theme.dart';

/// Labeled text field used on all auth screens, with an optional
/// show/hide toggle for passwords.
class AuthTextField extends StatefulWidget {
  final TextEditingController controller;
  final String label;
  final String? hint;
  final IconData icon;
  final bool isPassword;
  final TextInputType keyboardType;
  final TextInputAction textInputAction;
  final Iterable<String>? autofillHints;

  /// Hard input limit (no visible counter); mirrors the backend limits.
  final int? maxLength;
  final FormFieldValidator<String>? validator;
  final ValueChanged<String>? onFieldSubmitted;
  final ValueChanged<String>? onChanged;
  final FocusNode? focusNode;
  final bool enabled;
  final TextCapitalization textCapitalization;

  const AuthTextField({
    super.key,
    required this.controller,
    required this.label,
    required this.icon,
    this.hint,
    this.isPassword = false,
    this.keyboardType = TextInputType.text,
    this.textInputAction = TextInputAction.next,
    this.autofillHints,
    this.maxLength,
    this.validator,
    this.onFieldSubmitted,
    this.onChanged,
    this.focusNode,
    this.enabled = true,
    this.textCapitalization = TextCapitalization.none,
  });

  @override
  State<AuthTextField> createState() => _AuthTextFieldState();
}

class _AuthTextFieldState extends State<AuthTextField> {
  bool _obscured = true;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return TextFormField(
      controller: widget.controller,
      focusNode: widget.focusNode,
      enabled: widget.enabled,
      obscureText: widget.isPassword && _obscured,
      enableSuggestions: !widget.isPassword,
      autocorrect: false,
      keyboardType: widget.isPassword
          ? TextInputType.visiblePassword
          : widget.keyboardType,
      textInputAction: widget.textInputAction,
      textCapitalization: widget.textCapitalization,
      autofillHints: widget.autofillHints,
      inputFormatters: [
        if (widget.maxLength != null)
          LengthLimitingTextInputFormatter(widget.maxLength),
      ],
      validator: widget.validator,
      onFieldSubmitted: widget.onFieldSubmitted,
      onChanged: widget.onChanged,
      style: context.text.bodyLarge,
      decoration: InputDecoration(
        labelText: widget.label,
        hintText: widget.hint,
        errorMaxLines: 2,
        prefixIcon: Icon(widget.icon, size: 20),
        suffixIcon: widget.isPassword
            ? IconButton(
                onPressed: () => setState(() => _obscured = !_obscured),
                tooltip: _obscured
                    ? l10n.authShowPassword
                    : l10n.authHidePassword,
                icon: Icon(
                  _obscured
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                  size: 20,
                ),
              )
            : null,
      ),
    );
  }
}

/// Primary button that shows a spinner and stays disabled while loading.
class AuthSubmitButton extends StatelessWidget {
  final String label;
  final String loadingLabel;
  final bool isLoading;
  final VoidCallback? onPressed;

  const AuthSubmitButton({
    super.key,
    required this.label,
    required this.loadingLabel,
    required this.onPressed,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      enabled: !isLoading && onPressed != null,
      label: isLoading ? loadingLabel : label,
      excludeSemantics: true,
      child: FilledButton(
        onPressed: isLoading ? null : onPressed,
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 160),
          child: isLoading
              ? Row(
                  key: const ValueKey('loading'),
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.2,
                        color: context.colors.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                    const SizedBox(width: Gap.md),
                    Text(loadingLabel),
                  ],
                )
              : Text(label, key: const ValueKey('label')),
        ),
      ),
    );
  }
}
