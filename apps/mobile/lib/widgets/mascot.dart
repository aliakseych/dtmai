import 'package:flutter/material.dart';

enum MascotPose {
  straight,
  left,
  right,
  top,
  leftBottom,
  rightBottom,
  celebrate,
  sad,
  sleep,
  thinking,
  trophy,
  streak,
  wave,
  premium,
}

/// Temur, the Uzbek corsac fox.
class Mascot extends StatelessWidget {
  const Mascot({super.key, this.pose = MascotPose.straight, this.size = 120});
  final MascotPose pose;
  final double size;

  String get _asset => switch (pose) {
        MascotPose.straight => 'straight',
        MascotPose.left => 'left',
        MascotPose.right => 'right',
        MascotPose.top => 'top',
        MascotPose.leftBottom => 'left_bottom',
        MascotPose.rightBottom => 'right_bottom',
        MascotPose.celebrate => 'celebrate',
        MascotPose.sad => 'sad',
        MascotPose.sleep => 'sleep',
        MascotPose.thinking => 'thinking',
        MascotPose.trophy => 'trophy',
        MascotPose.streak => 'streak',
        MascotPose.wave => 'wave',
        MascotPose.premium => 'premium',
      };

  @override
  Widget build(BuildContext context) => ExcludeSemantics(
        child: Image.asset(
          'assets/brand/$_asset.png',
          width: size,
          height: size,
          fit: BoxFit.contain,
          errorBuilder: (_, __, ___) => SizedBox(width: size, height: size),
        ),
      );
}
