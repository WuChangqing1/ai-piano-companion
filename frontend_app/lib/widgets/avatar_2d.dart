import 'dart:math' as math;
import 'package:flutter/material.dart';

/// 2D 卡通数字人 — 可爱的钢琴小老师
/// speaking 为 true 时嘴巴做开合动画，眼睛会眨动
class Avatar2D extends StatefulWidget {
  final bool speaking;
  final double size;
  const Avatar2D({super.key, required this.speaking, this.size = 200});

  @override
  State<Avatar2D> createState() => _Avatar2DState();
}

class _Avatar2DState extends State<Avatar2D>
    with TickerProviderStateMixin {
  late AnimationController _mouthCtrl;
  late AnimationController _blinkCtrl;
  bool _wasSpeaking = false;

  @override
  void initState() {
    super.initState();
    _mouthCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 350),
    );

    _blinkCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
    );

    _scheduleBlink();
  }

  void _scheduleBlink() {
    Future.delayed(Duration(milliseconds: 2500 + math.Random().nextInt(2000)), () {
      if (!mounted) return;
      _blinkCtrl.forward().then((_) {
        if (mounted) _blinkCtrl.reverse();
      });
      _scheduleBlink();
    });
  }

  @override
  void didUpdateWidget(covariant Avatar2D oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.speaking != _wasSpeaking) {
      if (widget.speaking) {
        _mouthCtrl.repeat(reverse: true);
      } else {
        _mouthCtrl.stop();
        _mouthCtrl.animateTo(0, duration: const Duration(milliseconds: 200));
      }
      _wasSpeaking = widget.speaking;
    }
  }

  @override
  void dispose() {
    _mouthCtrl.dispose();
    _blinkCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge([_mouthCtrl, _blinkCtrl]),
      builder: (_, __) {
        final mouthOpen = widget.speaking ? _mouthCtrl.value : 0.0;
        return CustomPaint(
          size: Size(widget.size, widget.size),
          painter: _AvatarPainter(
            mouthOpen: mouthOpen,
            blinkValue: _blinkCtrl.value,
            speaking: widget.speaking,
          ),
        );
      },
    );
  }
}

class _AvatarPainter extends CustomPainter {
  final double mouthOpen;
  final double blinkValue;
  final bool speaking;

  _AvatarPainter({
    required this.mouthOpen,
    required this.blinkValue,
    required this.speaking,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final r = size.width / 2.2;

    // Glow effect when speaking
    if (speaking) {
      final glowPaint = Paint()
        ..color = const Color(0xFF8B5CF6).withValues(alpha: 0.08 + mouthOpen * 0.05)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 20);
      canvas.drawCircle(Offset(cx, cy), r * 1.15, glowPaint);
    }

    // Face with gradient
    final facePaint = Paint()
      ..shader = RadialGradient(
        colors: [
          const Color(0xFFFFF0DB),
          const Color(0xFFFFE0B2),
        ],
      ).createShader(Rect.fromCircle(center: Offset(cx, cy), radius: r));
    canvas.drawCircle(Offset(cx, cy), r, facePaint);

    // Hair (bob cut with bangs)
    final hairPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          const Color(0xFF5D4037),
          const Color(0xFF4E342E),
        ],
      ).createShader(Rect.fromLTWH(cx - r, cy - r * 1.4, r * 2, r * 1.6));

    final hairPath = Path()
      ..moveTo(cx - r * 1.05, cy + r * 0.1)
      ..quadraticBezierTo(cx - r * 1.1, cy - r * 0.8, cx - r * 0.6, cy - r * 1.15)
      ..quadraticBezierTo(cx, cy - r * 1.5, cx + r * 0.6, cy - r * 1.15)
      ..quadraticBezierTo(cx + r * 1.1, cy - r * 0.8, cx + r * 1.05, cy + r * 0.1)
      ..quadraticBezierTo(cx + r * 0.95, cy - r * 0.15, cx + r * 0.8, cy - r * 0.3)
      ..quadraticBezierTo(cx + r * 0.5, cy - r * 0.85, cx, cy - r * 0.95)
      ..quadraticBezierTo(cx - r * 0.5, cy - r * 0.85, cx - r * 0.8, cy - r * 0.3)
      ..quadraticBezierTo(cx - r * 0.95, cy - r * 0.15, cx - r * 1.05, cy + r * 0.1)
      ..close();
    canvas.drawPath(hairPath, hairPaint);

    // Bangs
    final bangPath = Path()
      ..moveTo(cx - r * 0.7, cy - r * 0.55)
      ..quadraticBezierTo(cx - r * 0.35, cy - r * 0.2, cx - r * 0.05, cy - r * 0.5)
      ..quadraticBezierTo(cx + r * 0.15, cy - r * 0.15, cx + r * 0.45, cy - r * 0.45)
      ..quadraticBezierTo(cx + r * 0.65, cy - r * 0.2, cx + r * 0.75, cy - r * 0.55)
      ..quadraticBezierTo(cx + r * 0.5, cy - r * 0.9, cx, cy - r * 1.0)
      ..quadraticBezierTo(cx - r * 0.5, cy - r * 0.9, cx - r * 0.7, cy - r * 0.55)
      ..close();
    canvas.drawPath(bangPath, hairPaint);

    // Blush
    final blushPaint = Paint()
      ..color = const Color(0xFFFFAB91).withValues(alpha: 0.4);
    canvas.drawCircle(Offset(cx - r * 0.55, cy + r * 0.18), r * 0.13, blushPaint);
    canvas.drawCircle(Offset(cx + r * 0.55, cy + r * 0.18), r * 0.13, blushPaint);

    // Eyes
    final eyePaint = Paint()..color = const Color(0xFF3E2723);

    if (blinkValue > 0.8) {
      // Blinking — draw lines
      final blinkPaint = Paint()
        ..color = const Color(0xFF3E2723)
        ..strokeWidth = r * 0.04
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(
        Offset(cx - r * 0.38, cy - r * 0.02),
        Offset(cx - r * 0.28, cy - r * 0.02),
        blinkPaint,
      );
      canvas.drawLine(
        Offset(cx + r * 0.28, cy - r * 0.02),
        Offset(cx + r * 0.38, cy - r * 0.02),
        blinkPaint,
      );
    } else {
      // Normal eyes
      final eyeHeight = r * 0.11 * (1.0 - blinkValue * 0.9);
      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(cx - r * 0.33, cy - r * 0.02),
          width: r * 0.18,
          height: eyeHeight * 2,
        ),
        eyePaint,
      );
      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(cx + r * 0.33, cy - r * 0.02),
          width: r * 0.18,
          height: eyeHeight * 2,
        ),
        eyePaint,
      );

      // Eye glints
      final glintPaint = Paint()..color = Colors.white;
      canvas.drawCircle(Offset(cx - r * 0.30, cy - r * 0.06), r * 0.035, glintPaint);
      canvas.drawCircle(Offset(cx + r * 0.36, cy - r * 0.06), r * 0.035, glintPaint);
      canvas.drawCircle(Offset(cx - r * 0.36, cy + r * 0.01), r * 0.018, glintPaint);
      canvas.drawCircle(Offset(cx + r * 0.30, cy + r * 0.01), r * 0.018, glintPaint);
    }

    // Eyebrows
    final browPaint = Paint()
      ..color = const Color(0xFF5D4037)
      ..strokeWidth = r * 0.035
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(
      Offset(cx - r * 0.42, cy - r * 0.18),
      Offset(cx - r * 0.24, cy - r * 0.22),
      browPaint,
    );
    canvas.drawLine(
      Offset(cx + r * 0.24, cy - r * 0.22),
      Offset(cx + r * 0.42, cy - r * 0.18),
      browPaint,
    );

    // Mouth
    final mouthCenterY = cy + r * 0.38;
    final mouthW = r * (0.28 - mouthOpen * 0.04);
    final mouthH = r * (0.05 + mouthOpen * 0.2);

    if (mouthOpen < 0.15) {
      // Smile
      final smilePaint = Paint()
        ..color = const Color(0xFFD84315)
        ..strokeWidth = r * 0.04
        ..strokeCap = StrokeCap.round
        ..style = PaintingStyle.stroke;
      canvas.drawArc(
        Rect.fromCenter(
          center: Offset(cx, mouthCenterY - r * 0.05),
          width: mouthW * 2,
          height: r * 0.15,
        ),
        0.1 * math.pi,
        0.8 * math.pi,
        false,
        smilePaint,
      );
    } else {
      // Open mouth
      final mouthPaint = Paint()
        ..color = const Color(0xFFD84315)
        ..style = PaintingStyle.fill;
      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(cx, mouthCenterY),
          width: mouthW * 2,
          height: mouthH * 2,
        ),
        mouthPaint,
      );
      // Tongue
      final tonguePaint = Paint()..color = const Color(0xFFFF8A80);
      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(cx, mouthCenterY + mouthH * 0.3),
          width: mouthW * 1.2,
          height: mouthH * 0.6,
        ),
        tonguePaint,
      );
    }

    // Musical notes (when speaking)
    if (speaking) {
      final notePaint = Paint()..style = PaintingStyle.fill;
      final time = DateTime.now().millisecondsSinceEpoch / 1000.0;

      for (int i = 0; i < 3; i++) {
        final phase = time * 1.5 + i * 2.1;
        final noteX = cx + r * (0.8 + 0.3 * math.sin(phase * 0.7 + i));
        final noteY = cy - r * (0.3 + 0.5 * ((phase * 0.3 + i * 0.3) % 1.0));
        final noteSize = r * (0.04 + 0.02 * math.sin(phase));
        final alpha = (1.0 - ((phase * 0.3 + i * 0.3) % 1.0)) * 0.5;

        notePaint.color = [
          const Color(0xFF8B5CF6),
          const Color(0xFFEC4899),
          const Color(0xFF3B82F6),
        ][i].withValues(alpha: alpha);

        canvas.drawCircle(Offset(noteX, noteY), noteSize, notePaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _AvatarPainter old) =>
      old.mouthOpen != mouthOpen ||
      old.blinkValue != blinkValue ||
      old.speaking != speaking;
}
