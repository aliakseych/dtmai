import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Flat 3D "chunky" surface: a face over a darker 4px bottom edge. Flutter forbids
/// rounded borders with non-uniform sides, so the edge is a second rounded box.
class Chunky extends StatelessWidget {
  const Chunky({
    super.key,
    required this.face,
    required this.edge,
    required this.child,
    this.pressed = false,
    this.borderColor,
    this.radius = Tokens.radius,
    this.padding = const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
  });

  final Color face;
  final Color edge;
  final Widget child;
  final bool pressed;
  final Color? borderColor;
  final double radius;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final lift = pressed ? 0.0 : Tokens.edge;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 60),
      padding: EdgeInsets.only(bottom: lift),
      margin: EdgeInsets.only(top: Tokens.edge - lift),
      decoration: BoxDecoration(color: edge, borderRadius: BorderRadius.circular(radius)),
      child: Container(
        padding: padding,
        decoration: BoxDecoration(
          color: face,
          borderRadius: BorderRadius.circular(radius),
          border: borderColor == null ? null : Border.all(color: borderColor!, width: Tokens.borderWidth),
        ),
        child: child,
      ),
    );
  }
}

/// Pressable wrapper that drives [Chunky.pressed].
class PressableChunky extends StatefulWidget {
  const PressableChunky({
    super.key,
    required this.builder,
    required this.onPressed,
  });

  final Widget Function(BuildContext context, bool pressed) builder;
  final VoidCallback? onPressed;

  @override
  State<PressableChunky> createState() => _PressableChunkyState();
}

class _PressableChunkyState extends State<PressableChunky> {
  bool _down = false;

  void _set(bool v) {
    if (widget.onPressed == null) return;
    setState(() => _down = v);
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapDown: (_) => _set(true),
      onTapUp: (_) => _set(false),
      onTapCancel: () => _set(false),
      onTap: widget.onPressed,
      child: widget.builder(context, _down),
    );
  }
}
