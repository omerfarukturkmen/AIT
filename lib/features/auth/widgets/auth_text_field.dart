import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'auth_palette.dart';

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

  OutlineInputBorder _border(Color color, [double width = 1]) {
    return OutlineInputBorder(
      borderRadius: BorderRadius.circular(14),
      borderSide: BorderSide(color: color, width: width),
    );
  }

  @override
  Widget build(BuildContext context) {
    final palette = AuthPalette.of(context);

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
      cursorColor: palette.focus,
      style: TextStyle(
        color: palette.text,
        fontSize: 15.5,
        fontWeight: FontWeight.w500,
      ),
      decoration: InputDecoration(
        labelText: widget.label,
        hintText: widget.hint,
        labelStyle: TextStyle(color: palette.textMuted),
        floatingLabelStyle: WidgetStateTextStyle.resolveWith(
          (states) => TextStyle(
            color: states.contains(WidgetState.error)
                ? palette.error
                : states.contains(WidgetState.focused)
                ? palette.focus
                : palette.textMuted,
            fontWeight: FontWeight.w600,
          ),
        ),
        hintStyle: TextStyle(
          color: palette.textMuted.withValues(alpha: 0.75),
          fontWeight: FontWeight.w400,
        ),
        filled: true,
        fillColor: palette.fieldFill,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 16,
        ),
        prefixIcon: Icon(widget.icon, size: 20),
        prefixIconColor: WidgetStateColor.resolveWith(
          (states) => states.contains(WidgetState.focused)
              ? palette.focus
              : states.contains(WidgetState.error)
              ? palette.error
              : palette.textMuted,
        ),
        suffixIcon: widget.isPassword
            ? IconButton(
                onPressed: () => setState(() => _obscured = !_obscured),
                tooltip: _obscured ? 'Şifreyi göster' : 'Şifreyi gizle',
                icon: Icon(
                  _obscured
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                  size: 20,
                  color: palette.textMuted,
                ),
              )
            : null,
        errorStyle: TextStyle(
          color: palette.error,
          fontSize: 12.5,
          fontWeight: FontWeight.w600,
        ),
        errorMaxLines: 2,
        border: _border(palette.fieldBorder),
        enabledBorder: _border(palette.fieldBorder),
        disabledBorder: _border(palette.fieldBorder.withValues(alpha: 0.5)),
        focusedBorder: _border(palette.focus, 1.8),
        errorBorder: _border(palette.error),
        focusedErrorBorder: _border(palette.error, 1.8),
      ),
    );
  }
}
