import 'dart:math' as math;
import 'package:flutter/material.dart';

/// 2D 卡通数字人 - 用 CustomPainter 画一个简易表情,
/// speaking 为 true 时嘴巴会做开合动画。
/// 真实接入 Lottie/SVG 时,在此替换为 Lottie.asset。
class Avatar2D extends StatefulWidget {
  final bool speaking;
  final double size;
  const Avatar2D({super.key, required this.speaking, this.size = 200});

  @override
  State<Avatar2D> createState() => _Avatar2DState();
}

class _Avatar2DState extends State<Avatar2D>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) {
        final mouthOpen = widget.speaking ? _ctrl.value : 0.0;
        return CustomPaint(
          size: Size(widget.size, widget.size),
          painter: _AvatarPainter(mouthOpen: mouthOpen),
        );
      },
    );
  }
}

class _AvatarPainter extends CustomPainter {
  final double mouthOpen;
  _AvatarPainter({required this.mouthOpen});

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final r = size.width / 2.2;

    // 脸
    final face = Paint()..color = const Color(0xFFFFE0B2);
    canvas.drawCircle(Offset(cx, cy), r, face);

    // 头发
    final hair = Paint()..color = const Color(0xFF6D4C41);
    final hairPath = Path()
      ..moveTo(cx - r, cy)
      ..quadraticBezierTo(cx, cy - r * 1.6, cx + r, cy)
      ..lineTo(cx + r * 0.9, cy - r * 0.2)
      ..quadraticBezierTo(cx, cy - r * 1.0, cx - r * 0.9, cy - r * 0.2)
      ..close();
    canvas.drawPath(hairPath, hair);

    // 腮红
    final blush = Paint()..color = const Color(0xFFFFAB91).withOpacity(0.5);
    canvas.drawCircle(Offset(cx - r * 0.55, cy + r * 0.15), r * 0.12, blush);
    canvas.drawCircle(Offset(cx + r * 0.55, cy + r * 0.15), r * 0.12, blush);

    // 眼睛
    final eye = Paint()..color = const Color(0xFF3E2723);
    canvas.drawCircle(Offset(cx - r * 0.35, cy - r * 0.05), r * 0.09, eye);
    canvas.drawCircle(Offset(cx + r * 0.35, cy - r * 0.05), r * 0.09, eye);
    final glint = Paint()..color = Colors.white;
    canvas.drawCircle(Offset(cx - r * 0.32, cy - r * 0.08), r * 0.025, glint);
    canvas.drawCircle(Offset(cx + r * 0.38, cy - r * 0.08), r * 0.025, glint);

    // 嘴巴(说话时上下张开)
    final mouth = Paint()
      ..color = const Color(0xFFD84315)
      ..style = PaintingStyle.fill;
    final mouthH = r * (0.06 + mouthOpen * 0.18);
    final mouthW = r * (0.32 - mouthOpen * 0.06);
    final mouthRect = Rect.fromCenter(
      center: Offset(cx, cy + r * 0.42),
      width: mouthW,
      height: mouthH,
    );
    canvas.drawArc(mouthRect, 0, math.pi * 2, true, mouth);
  }

  @override
  bool shouldRepaint(covariant _AvatarPainter old) =>
      old.mouthOpen != mouthOpen;
}
