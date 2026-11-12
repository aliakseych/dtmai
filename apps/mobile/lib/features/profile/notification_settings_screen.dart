import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';

final notifyPrefsProvider = FutureProvider.autoDispose<NotifyPrefs>((ref) => ref.watch(apiProvider).notifyPrefs());

class NotificationSettingsScreen extends ConsumerStatefulWidget {
  const NotificationSettingsScreen({super.key});

  @override
  ConsumerState<NotificationSettingsScreen> createState() => _State();
}

class _State extends ConsumerState<NotificationSettingsScreen> {
  NotifyPrefs? _draft;
  bool _saving = false;

  static const _channels = ['telegram', 'push', 'email'];
  static const _kinds = ['streak_reminder', 'league_ending', 'daily_question'];

  String _channelLabel(BuildContext c, String k) {
    final l = c.l10n;
    return switch (k) { 'telegram' => l.channelTelegram, 'push' => l.channelPush, _ => l.channelEmail };
  }

  String _kindLabel(BuildContext c, String k) {
    final l = c.l10n;
    return switch (k) {
      'streak_reminder' => l.kindStreakReminder,
      'league_ending' => l.kindLeagueEnding,
      _ => l.kindDailyQuestion,
    };
  }

  List<String> _toggle(List<String> list, String v, bool on) =>
      on ? [...list.where((e) => e != v), v] : list.where((e) => e != v).toList();

  TimeOfDay _parse(String s) {
    final p = s.split(':');
    return TimeOfDay(hour: int.tryParse(p.first) ?? 0, minute: p.length > 1 ? int.tryParse(p[1]) ?? 0 : 0);
  }

  String _fmt(TimeOfDay t) => '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}:00';

  NotifyPrefs _withQuiet(NotifyPrefs p, {String? start, String? end}) => NotifyPrefs(
        enabled: p.enabled,
        channels: p.channels,
        kinds: p.kinds,
        maxPerDay: p.maxPerDay,
        quietStart: start ?? p.quietStart,
        quietEnd: end ?? p.quietEnd,
      );

  Future<void> _save(NotifyPrefs p) async {
    final l = context.l10n;
    setState(() => _saving = true);
    try {
      final saved = await ref.read(apiProvider).saveNotifyPrefs(p);
      if (!mounted) return;
      setState(() => _draft = saved);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.saved)));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(apiErrorMessage(e, l.errorGeneric))));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final prefs = ref.watch(notifyPrefsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.notificationSettings)),
      body: AsyncView<NotifyPrefs>(
        value: prefs,
        onRetry: () => ref.invalidate(notifyPrefsProvider),
        builder: (loaded) {
          final p = _draft ?? loaded;
          return ListView(padding: const EdgeInsets.all(16), children: [
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(l.notificationSettings, style: const TextStyle(fontWeight: FontWeight.w800)),
              value: p.enabled,
              onChanged: (v) => setState(() => _draft = p.copyWith(enabled: v)),
            ),
            const SizedBox(height: 8),
            Wrap(spacing: 8, children: [
              for (final c in _channels)
                FilterChip(
                  label: Text(_channelLabel(context, c)),
                  selected: p.channels.contains(c),
                  onSelected: p.enabled ? (v) => setState(() => _draft = p.copyWith(channels: _toggle(p.channels, c, v))) : null,
                ),
            ]),
            const SizedBox(height: 12),
            Wrap(spacing: 8, children: [
              for (final k in _kinds)
                FilterChip(
                  label: Text(_kindLabel(context, k)),
                  selected: p.kinds.contains(k),
                  onSelected: p.enabled ? (v) => setState(() => _draft = p.copyWith(kinds: _toggle(p.kinds, k, v))) : null,
                ),
            ]),
            const SizedBox(height: 16),
            Text('${l.maxPerDay}: ${p.maxPerDay}', style: const TextStyle(fontWeight: FontWeight.w700)),
            Slider(
              min: 0,
              max: 10,
              divisions: 10,
              value: p.maxPerDay.clamp(0, 10).toDouble(),
              label: '${p.maxPerDay}',
              onChanged: p.enabled ? (v) => setState(() => _draft = p.copyWith(maxPerDay: v.round())) : null,
            ),
            Text(l.quietHours, style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Row(children: [
              for (final isStart in [true, false]) ...[
                Expanded(
                  child: OutlinedButton(
                    onPressed: p.enabled
                        ? () async {
                            final t = await showTimePicker(
                              context: context,
                              initialTime: _parse(isStart ? p.quietStart : p.quietEnd),
                            );
                            if (t != null) {
                              setState(() => _draft = isStart ? _withQuiet(p, start: _fmt(t)) : _withQuiet(p, end: _fmt(t)));
                            }
                          }
                        : null,
                    child: Text((isStart ? p.quietStart : p.quietEnd).substring(0, 5)),
                  ),
                ),
                if (isStart) const Padding(padding: EdgeInsets.symmetric(horizontal: 8), child: Text('–')),
              ],
            ]),
            const SizedBox(height: 24),
            ChunkyButton(label: l.save, loading: _saving, onPressed: () => _save(p)),
          ]);
        },
      ),
    );
  }
}
