import 'package:flutter_svg/flutter_svg.dart';
import 'package:material_ui/material_ui.dart';

/// The one DTM AI logo (design file "DTM AI Logo.svg", brand #100FA0), 763:216.
class Logo extends StatelessWidget {
  const Logo({super.key, this.height = 40});
  final double height;

  @override
  Widget build(BuildContext context) => SvgPicture.asset(
        'assets/brand/logo.svg',
        height: height,
        fit: BoxFit.contain,
        semanticsLabel: 'DTM AI',
      );
}
