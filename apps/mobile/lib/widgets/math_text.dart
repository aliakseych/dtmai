import 'package:material_ui/material_ui.dart';
import 'package:flutter_math_fork/flutter_math.dart';

/// Renders text containing inline `$...$` TeX segments.
class MathText extends StatelessWidget {
  const MathText(this.source, {super.key, this.style});
  final String source;
  final TextStyle? style;

  static final _re = RegExp(r'(?<!\\)\$(?=\S)((?:[^$\\]|\\.)+?)(?<=\S)(?<!\\)\$');

  static String _plain(String s) => s.replaceAll(r'\$', r'$');

  @override
  Widget build(BuildContext context) {
    final base = style ?? DefaultTextStyle.of(context).style;
    final spans = <InlineSpan>[];
    var last = 0;
    for (final m in _re.allMatches(source)) {
      if (m.start > last) spans.add(TextSpan(text: _plain(source.substring(last, m.start))));
      spans.add(WidgetSpan(
        alignment: PlaceholderAlignment.middle,
        child: Math.tex(
          m.group(1)!,
          textStyle: base,
          onErrorFallback: (_) => Text(m.group(0)!, style: base),
        ),
      ));
      last = m.end;
    }
    if (last < source.length) spans.add(TextSpan(text: _plain(source.substring(last))));
    return Text.rich(TextSpan(style: base, children: spans));
  }
}
