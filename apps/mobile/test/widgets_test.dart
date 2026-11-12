import 'package:dtmai/core/models.dart';
import 'package:dtmai/widgets/chunky_button.dart';
import 'package:dtmai/widgets/option_tile.dart';
import 'package:dtmai/widgets/stat_chips.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: Center(child: child)));

void main() {
  group('ChunkyButton', () {
    testWidgets('fires onPressed and meets 44px tap target', (t) async {
      var taps = 0;
      await t.pumpWidget(_wrap(ChunkyButton(label: 'CHECK', onPressed: () => taps++)));
      expect(find.text('CHECK'), findsOneWidget);
      expect(t.getSize(find.byType(ChunkyButton)).height, greaterThanOrEqualTo(44));
      await t.tap(find.byType(ChunkyButton));
      await t.pumpAndSettle();
      expect(taps, 1);
    });

    testWidgets('disabled and loading do not fire', (t) async {
      var taps = 0;
      await t.pumpWidget(_wrap(ChunkyButton(label: 'GO', onPressed: null)));
      await t.tap(find.byType(ChunkyButton));
      await t.pumpAndSettle();
      expect(taps, 0);
      await t.pumpWidget(_wrap(ChunkyButton(label: 'GO', loading: true, onPressed: () => taps++)));
      await t.tap(find.byType(ChunkyButton), warnIfMissed: false);
      await t.pump();
      expect(taps, 0);
    });
  });

  group('OptionTile', () {
    testWidgets('renders text, hotkey and taps', (t) async {
      var taps = 0;
      await t.pumpWidget(_wrap(OptionTile(
        text: 'Paris',
        hotkey: 'A',
        status: OptionStatus.idle,
        onTap: () => taps++,
      )));
      expect(find.text('Paris'), findsOneWidget);
      expect(find.text('A'), findsOneWidget);
      expect(t.getSize(find.byType(OptionTile)).height, greaterThanOrEqualTo(44));
      await t.tap(find.byType(OptionTile));
      await t.pumpAndSettle();
      expect(taps, 1);
    });

    testWidgets('exposes selected state in semantics', (t) async {
      final h = t.ensureSemantics();
      await t.pumpWidget(_wrap(OptionTile(text: 'Rome', status: OptionStatus.selected, onTap: () {})));
      expect(
        t.getSemantics(find.byType(OptionTile)),
        matchesSemantics(
          label: 'Rome',
          isButton: true,
          isSelected: true,
          isEnabled: true,
          hasEnabledState: true,
          hasSelectedState: true,
          hasTapAction: true,
        ),
      );
      h.dispose();
    });
  });

  group('StatChips', () {
    Stats stats({bool unlimited = false}) => Stats(
          gems: 120,
          hearts: Hearts(count: 4, max: 5, unlimited: unlimited),
          streak: 7,
          streakLongest: 9,
          streakActiveToday: true,
          streakAtRisk: false,
          xpToday: 10,
          xpTotal: 500,
          lessonsCompleted: 3,
        );

    testWidgets('shows streak, gems and hearts', (t) async {
      await t.pumpWidget(_wrap(StatChips(stats: stats())));
      expect(find.text('7'), findsOneWidget);
      expect(find.text('120'), findsOneWidget);
      expect(find.text('4'), findsOneWidget);
    });

    testWidgets('shows infinity for unlimited hearts', (t) async {
      await t.pumpWidget(_wrap(StatChips(stats: stats(unlimited: true))));
      expect(find.text('∞'), findsOneWidget);
    });
  });
}
