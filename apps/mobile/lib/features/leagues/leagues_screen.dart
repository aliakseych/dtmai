import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/guest_gate.dart';
import 'league_providers.dart';

class LeaguesScreen extends StatelessWidget {
  const LeaguesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l.leagues),
          bottom: TabBar(tabs: [Tab(text: l.tabLeague), Tab(text: l.tabFriends), Tab(text: l.tabLyceum)]),
        ),
        body: GuestGate(
          requireAccount: true,
          child: TabBarView(children: [
            const _LeagueTab(),
            const _BoardTab(kind: BoardKind.friends),
            const _BoardTab(kind: BoardKind.lyceum),
          ]),
        ),
      ),
    );
  }
}

class _BoardTab extends ConsumerStatefulWidget {
  const _BoardTab({required this.kind});
  final BoardKind kind;

  @override
  ConsumerState<_BoardTab> createState() => _BoardTabState();
}

class _BoardTabState extends ConsumerState<_BoardTab> with AutomaticKeepAliveClientMixin {
  String _period = 'week';

  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final l = context.l10n;
    final key = (widget.kind, _period);
    return Column(children: [
      Padding(
        padding: const EdgeInsets.all(16),
        child: SegmentedButton<String>(
          segments: [
            ButtonSegment(value: 'week', label: Text(l.weekly)),
            ButtonSegment(value: 'all', label: Text(l.allTime)),
          ],
          selected: {_period},
          onSelectionChanged: (s) => setState(() => _period = s.first),
        ),
      ),
      Expanded(
        child: AsyncView<Board>(
          value: ref.watch(boardProvider(key)),
          isEmpty: (b) => b.rows.isEmpty,
          onRetry: () => ref.invalidate(boardProvider(key)),
          builder: (b) => RefreshIndicator(
            onRefresh: () async => ref.invalidate(boardProvider(key)),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              children: [
                if (b.myRank != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text('${l.rank}: ${b.myRank}', style: const TextStyle(color: Tokens.textMuted, fontWeight: FontWeight.w800)),
                  ),
                for (final (i, r) in b.rows.indexed)
                  Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
                      borderRadius: BorderRadius.circular(Tokens.radius),
                    ),
                    child: Row(children: [
                      SizedBox(width: 32, child: Text('${i + 1}', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16))),
                      Expanded(child: Text(r.name, style: const TextStyle(fontWeight: FontWeight.w800))),
                      Text('${r.xp} ${l.xp}', style: const TextStyle(color: Tokens.goldText, fontWeight: FontWeight.w800)),
                    ]),
                  ),
              ],
            ),
          ),
        ),
      ),
    ]);
  }
}

class _LeagueTab extends ConsumerWidget {
  const _LeagueTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final tag = context.localeTag;
    final league = ref.watch(leagueProvider);
    return AsyncView<League?>(
          value: league,
          isEmpty: (d) => d == null || d.rows.isEmpty,
          onRetry: () => ref.invalidate(leagueProvider),
          builder: (lg) {
            final ends = lg!.endsAt?.difference(DateTime.now());
            return RefreshIndicator(
              onRefresh: () async => ref.invalidate(leagueProvider),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Text(l.weeklyLeague, style: const TextStyle(color: Tokens.textMuted, fontWeight: FontWeight.w800)),
                  if (lg.tier != null) Text(pickName(lg.tier!.name, tag), style: Theme.of(context).textTheme.headlineMedium),
                  if (ends != null && !ends.isNegative)
                    Text(
                        l.leagueEndsIn(ends.inDays > 0
                            ? l.durationDaysHours(ends.inDays, ends.inHours % 24)
                            : l.durationHoursMinutes(ends.inHours, ends.inMinutes % 60)),
                        style: const TextStyle(color: Tokens.textMuted)),
                  const SizedBox(height: 16),
                  for (final e in lg.rows)
                    Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: e.isMe ? Tokens.blueSoft : _zone(e.zone),
                        border: Border.all(color: e.isMe ? Tokens.blue : Tokens.border, width: Tokens.borderWidth),
                        borderRadius: BorderRadius.circular(Tokens.radius),
                      ),
                      child: Row(children: [
                        SizedBox(width: 32, child: Text('${e.rank}', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16))),
                        Expanded(child: Text(e.name, style: const TextStyle(fontWeight: FontWeight.w800))),
                        Text('${e.xp} ${l.xp}', style: const TextStyle(color: Tokens.goldText, fontWeight: FontWeight.w800)),
                      ]),
                    ),
                ],
              ),
            );
          },
    );
  }

  Color _zone(String zone) => switch (zone) {
        'promote' || 'promotion' => Tokens.greenSoft,
        'demote' || 'demotion' => Tokens.redSoft,
        _ => Colors.white,
      };
}
