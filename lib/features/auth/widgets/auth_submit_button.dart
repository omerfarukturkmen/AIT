import 'package:flutter/material.dart';

import '../../../core/constants/app_colors.dart';

/// Primary call-to-action for the auth forms with hover, pressed, focus,
/// loading and disabled states.
class AuthSubmitButton extends StatefulWidget {
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
  State<AuthSubmitButton> createState() => _AuthSubmitButtonState();
}

class _AuthSubmitButtonState extends State<AuthSubmitButton> {
  bool _hovered = false;
  bool _pressed = false;
  bool _focused = false;

  bool get _enabled => widget.onPressed != null && !widget.isLoading;

  @override
  Widget build(BuildContext context) {
    final colors = _hovered && _enabled
        ? const [Color(0xFF7C3AED), Color(0xFF2563EB)]
        : const [AppColors.primary, Color(0xFF3B82F6)];

    return Semantics(
      button: true,
      enabled: _enabled,
      label: widget.isLoading ? widget.loadingLabel : widget.label,
      excludeSemantics: true,
      child: AnimatedOpacity(
        duration: const Duration(milliseconds: 150),
        opacity: widget.onPressed == null && !widget.isLoading ? 0.5 : 1,
        child: AnimatedScale(
          duration: const Duration(milliseconds: 120),
          scale: _pressed ? 0.985 : 1,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            height: 52,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: colors,
              ),
              border: Border.all(
                color: _focused ? Colors.white : Colors.transparent,
                width: 2,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.primary.withValues(
                    alpha: !_enabled
                        ? 0
                        : _hovered
                        ? 0.38
                        : 0.24,
                  ),
                  blurRadius: _hovered ? 22 : 16,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Material(
              type: MaterialType.transparency,
              child: InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: _enabled ? widget.onPressed : null,
                onHover: (value) => setState(() => _hovered = value),
                onFocusChange: (value) => setState(() => _focused = value),
                onHighlightChanged: (value) => setState(() => _pressed = value),
                splashColor: Colors.white.withValues(alpha: 0.12),
                highlightColor: Colors.white.withValues(alpha: 0.06),
                mouseCursor: _enabled
                    ? SystemMouseCursors.click
                    : SystemMouseCursors.basic,
                child: Center(
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 180),
                    child: widget.isLoading
                        ? Row(
                            key: const ValueKey('loading'),
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const SizedBox(
                                height: 18,
                                width: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2.2,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Text(widget.loadingLabel, style: _labelStyle),
                            ],
                          )
                        : Text(
                            widget.label,
                            key: const ValueKey('label'),
                            style: _labelStyle,
                          ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  static const TextStyle _labelStyle = TextStyle(
    color: Colors.white,
    fontSize: 15.5,
    fontWeight: FontWeight.w700,
    letterSpacing: 0.2,
  );
}
