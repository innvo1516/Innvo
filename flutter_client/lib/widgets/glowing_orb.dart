import 'dart:math' as math;
import 'package:flutter/material.dart';

class GlowingOrb extends StatefulWidget {
  final bool isThinking;
  final double size;

  const GlowingOrb({
    Key? key,
    this.isThinking = false,
    this.size = 140.0,
  }) : super(key: key);

  @override
  State<GlowingOrb> createState() => _GlowingOrbState();
}

class _GlowingOrbState extends State<GlowingOrb> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final double pulse = widget.isThinking ? _controller.value * 1.3 : _controller.value;
        final double currentSize = widget.size + (pulse * 15.0);

        return Center(
          child: Container(
            width: currentSize,
            height: currentSize,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: widget.isThinking
                    ? [
                        const Color(0xFF00FFD1),
                        const Color(0xFF0088FF).withOpacity(0.8),
                        const Color(0xFF7000FF).withOpacity(0.3),
                        Colors.transparent,
                      ]
                    : [
                        const Color(0xFF00E5FF),
                        const Color(0xFF0072FF).withOpacity(0.7),
                        const Color(0xFF0D1B2A).withOpacity(0.2),
                        Colors.transparent,
                      ],
                stops: const [0.2, 0.5, 0.8, 1.0],
              ),
              boxShadow: [
                BoxShadow(
                  color: widget.isThinking
                      ? const Color(0xFF00FFD1).withOpacity(0.6)
                      : const Color(0xFF00E5FF).withOpacity(0.4),
                  blurRadius: 35.0 + (pulse * 15.0),
                  spreadRadius: 8.0 + (pulse * 8.0),
                ),
              ],
            ),
            child: Center(
              child: Container(
                width: widget.size * 0.45,
                height: widget.size * 0.45,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFF0A0F1D),
                  border: Border.all(
                    color: const Color(0xFF00E5FF),
                    width: 2.0,
                  ),
                ),
                child: Center(
                  child: Icon(
                    widget.isThinking ? Icons.wifi_protected_setup_rounded : Icons.graphic_eq_rounded,
                    color: const Color(0xFF00E5FF),
                    size: widget.size * 0.25,
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
