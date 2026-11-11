import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../profile/profile_providers.dart';
import 'lyceum_providers.dart';

/// Explorer: quotas / applications / competition per speciality for a lyceum.
class LyceumsScreen extends ConsumerStatefulWidget {
  const LyceumsScreen({super.key});

  @override
  ConsumerState<LyceumsScreen> createState() => _LyceumsScreenState();
}

class _LyceumsScreenState extends ConsumerState<LyceumsScreen> {
  Timer? _debounce;

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  void _onSearch(String v) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () => ref.read(lyceumQueryProvider.notifier).set(v));
  }

  void _open(String id) => showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (_) => DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.7,
          maxChildSize: 0.95,
          builder: (_, controller) => _LyceumSheet(lyceumId: id, controller: controller),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final tag = context.localeTag;
    final lyceums = ref.watch(lyceumsProvider);
    final me = ref.watch(meProvider).value;
    final selected = me?.targetLyceumId;

    return Scaffold(
      appBar: AppBar(title: Text(l.lyceums)),
      body: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
          child: TextField(
            decoration: InputDecoration(prefixIcon: const Icon(Icons.search_rounded), hintText: l.search),
            onChanged: _onSearch,
          ),
        ),
        Expanded(
          child: AsyncView<List<Lyceum>>(
            value: lyceums,
            isEmpty: (d) => d.isEmpty,
            onRetry: () => ref.invalidate(lyceumsProvider),
            builder: (list) => ListView(
              padding: const EdgeInsets.all(16),
              children: [
                for (final c in list)
                  Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: c.id == selected ? Tokens.blueSoft : Colors.white,
                      border: Border.all(color: c.id == selected ? Tokens.blue : Tokens.border, width: Tokens.borderWidth),
                      borderRadius: BorderRadius.circular(Tokens.radius),
                    ),
                    child: ListTile(
                      title: Text(pickName(c.names, tag), style: const TextStyle(fontWeight: FontWeight.w800)),
                      subtitle: Text('${l.quota}: ${c.quota} · ${l.applications}: ${c.applications}'),
                      trailing: c.id == me?.targetLyceumId ? const Icon(Icons.flag_rounded, color: Tokens.blue) : null,
                      onTap: () => _open(c.id),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ]),
    );
  }
}

class _LyceumSheet extends ConsumerStatefulWidget {
  const _LyceumSheet({required this.lyceumId, required this.controller});
  final String lyceumId;
  final ScrollController controller;

  @override
  ConsumerState<_LyceumSheet> createState() => _LyceumSheetState();
}

class _LyceumSheetState extends ConsumerState<_LyceumSheet> {
  int? _year;
  bool _saving = false;

  Future<void> _setTarget(String id) async {
    setState(() => _saving = true);
    try {
      await ref.read(apiProvider).patchMe(targetLyceumId: id);
      ref.invalidate(meProvider);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(apiErrorMessage(e, context.l10n.errorGeneric))));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lyceumId = widget.lyceumId;
    final isTarget = ref.watch(meProvider).value?.targetLyceumId == lyceumId;
    final l = context.l10n;
    final tag = context.localeTag;
    final detail = ref.watch(lyceumDetailProvider(lyceumId));
    return detail.when(
      loading: () => const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator())),
      error: (e, _) => TextButton(
        onPressed: () => ref.invalidate(lyceumDetailProvider(lyceumId)),
        child: Text('${l.errorGeneric} · ${l.retry}'),
      ),
      data: (d) {
        final years = d.stats.map((s) => s.year).toSet().toList()..sort((a, b) => b.compareTo(a));
        final year = _year ?? (years.isEmpty ? null : years.first);
        final rows = d.stats.where((s) => s.year == year).toList();
        return ListView(controller: widget.controller, padding: const EdgeInsets.fromLTRB(16, 0, 16, 24), children: [
          Text(pickName(d.names, tag), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          if (!isTarget)
            ChunkyButton(label: l.setTarget, loading: _saving, tone: ChunkyTone.blue, onPressed: () => _setTarget(lyceumId)),
          const SizedBox(height: 8),
          Wrap(spacing: 8, children: [
            for (final y in years)
              ChoiceChip(label: Text('$y'), selected: y == year, onSelected: (_) => setState(() => _year = y)),
          ]),
          for (final s in rows)
            Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
                borderRadius: BorderRadius.circular(Tokens.radius),
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(s.name, style: const TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 6),
                Row(children: [
                  _kv(l.quota, '${s.quota}', Tokens.text),
                  _kv(l.applications, '${s.applications}', Tokens.text),
                  if (s.competitionRatio != null) _kv(l.competition, s.competitionRatio!.toStringAsFixed(1), Tokens.orange),
                  if (s.passingScore != null) _kv(l.passingScore, s.passingScore!.toStringAsFixed(1), Tokens.greenEdge),
                ]),
              ]),
            ),
        ]);
      },
    );
  }

  Widget _kv(String k, String v, Color c) => Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(k, style: const TextStyle(color: Tokens.textMuted, fontSize: 12)),
          Text(v, style: TextStyle(fontWeight: FontWeight.w800, color: c)),
        ]),
      );
}
