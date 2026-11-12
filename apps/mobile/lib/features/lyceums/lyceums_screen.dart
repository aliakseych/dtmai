import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/l10n_ext.dart';
import '../../core/media_url.dart';
import '../../core/models.dart';
import '../../l10n/app_localizations.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../profile/profile_providers.dart';
import '../../widgets/priority_picker.dart';
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

  Future<void> _saveDreams(List<String> ids) async {
    try {
      await ref.read(apiProvider).patchMe(dreamLyceumIds: ids);
      ref.invalidate(meProvider);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(apiErrorMessage(e, context.l10n.errorGeneric))));
      }
    }
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
    final names = {for (final x in ref.watch(allLyceumsProvider).value ?? lyceums.value ?? const <Lyceum>[]) x.id: x.names};
    final cityNames = {for (final c in ref.watch(citiesProvider).value ?? const <City>[]) c.code: pickName(c.names, tag)};
    final dreams = me?.dreamLyceumIds ?? const <String>[];

    return Scaffold(
      appBar: AppBar(title: Text(l.lyceums)),
      body: Column(children: [
        Padding(
          padding: EdgeInsets.fromLTRB(_hPad(context), 8, _hPad(context), 8),
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
              padding: EdgeInsets.symmetric(horizontal: _hPad(context), vertical: 16),
              children: [
                if (dreams.isNotEmpty) ...[
                  Text(l.dreamLyceums, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  PriorityPicker(
                    ids: dreams,
                    nameOf: (id) => pickName(names[id] ?? const {}, tag),
                    onChanged: (v) => _saveDreams(v),
                  ),
                  const SizedBox(height: 16),
                ],
                for (final c in list)
                  Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(
                      color: dreams.contains(c.id) ? Tokens.blueSoft : Colors.white,
                      border: Border.all(color: dreams.contains(c.id) ? Tokens.blue : Tokens.border, width: Tokens.borderWidth),
                      borderRadius: BorderRadius.circular(Tokens.radius),
                    ),
                    child: ListTile(
                      title: Text(pickName(c.names, tag), style: const TextStyle(fontWeight: FontWeight.w800)),
                      leading: _LyceumLogo(url: c.logoUrl),
                      subtitle: Text([
                        if (c.city != null && cityNames[c.city] != null) cityNames[c.city]!,
                        '${l.quota}: ${c.quota} · ${l.applications}: ${c.applications}'
                            '${c.competition != null ? ' · ${l.competition}: ${c.competition!.toStringAsFixed(1)}${c.competitionYear != null ? ' (${c.competitionYear})' : ''}' : ''}',
                        if (c.dormitoryStatus != DormitoryStatus.unknown) dormitoryLabel(l, c.dormitoryStatus),
                      ].join('\n')),
                      isThreeLine: c.city != null || c.dormitoryStatus != DormitoryStatus.unknown,
                      trailing: dreams.contains(c.id)
                          ? Row(mainAxisSize: MainAxisSize.min, children: [
                              const Icon(Icons.flag_rounded, color: Tokens.blue),
                              Text('${dreams.indexOf(c.id) + 1}', style: const TextStyle(fontWeight: FontWeight.w800, color: Tokens.brand)),
                            ])
                          : null,
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

/// Horizontal padding that keeps list content within a readable max width.
double _hPad(BuildContext context) {
  final w = MediaQuery.sizeOf(context).width;
  return w > 720 ? (w - 720) / 2 : 16;
}

String dormitoryLabel(AppLocalizations l, DormitoryStatus s) => switch (s) {
      DormitoryStatus.available => l.dormitoryAvailable,
      DormitoryStatus.limited => l.dormitoryLimited,
      DormitoryStatus.none => l.dormitoryNone,
      DormitoryStatus.unknown => l.dormitoryUnknown,
    };

class _LyceumLogo extends StatelessWidget {
  const _LyceumLogo({this.url});
  final String? url;

  @override
  Widget build(BuildContext context) {
    final fallback = Image.asset('assets/brand/icon_lyceum.png', width: 40, height: 40);
    final src = resolveMedia(url);
    if (src == null) return fallback;
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: Image.network(src, width: 40, height: 40, fit: BoxFit.cover, errorBuilder: (_, _, _) => fallback),
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

  Future<void> _toggleDream(String id, List<String> current) async {
    final l = context.l10n;
    final next = current.contains(id) ? current.where((x) => x != id).toList() : [...current, id];
    if (next.length > maxDreamLyceums) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.tooManyDreams)));
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(apiProvider).patchMe(dreamLyceumIds: next);
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
    final dreams = ref.watch(meProvider).value?.dreamLyceumIds ?? const <String>[];
    final isTarget = dreams.contains(lyceumId);
    final l = context.l10n;
    final tag = context.localeTag;
    final detail = ref.watch(lyceumDetailProvider(lyceumId));
    final cities = {for (final c in ref.watch(citiesProvider).value ?? const <City>[]) c.code: pickName(c.names, tag)};
    String? cityName(String? code) => code == null ? null : cities[code];
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
          if (resolveMedia(d.campusPhotoUrl) != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(Tokens.radius),
                child: Image.network(resolveMedia(d.campusPhotoUrl)!, height: 160, width: double.infinity, fit: BoxFit.cover, errorBuilder: (_, _, _) => const SizedBox.shrink()),
              ),
            ),
          Row(children: [
            _LyceumLogo(url: d.logoUrl),
            const SizedBox(width: 12),
            Expanded(child: Text(pickName(d.names, tag), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800))),
          ]),
          if (d.city != null && cityName(d.city) != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Row(children: [
                const Icon(Icons.place_rounded, size: 16, color: Tokens.textMuted),
                const SizedBox(width: 4),
                Text(cityName(d.city)!, style: const TextStyle(color: Tokens.textMuted, fontWeight: FontWeight.w700)),
              ]),
            ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Tokens.blueSoft,
              borderRadius: BorderRadius.circular(Tokens.radius),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.bed_rounded, size: 20, color: Tokens.brand),
                const SizedBox(width: 8),
                Expanded(child: Text('${l.dormitory}: ${dormitoryLabel(l, d.dormitoryStatus)}', style: const TextStyle(fontWeight: FontWeight.w800))),
              ]),
              if (pickName(d.dormitoryDescription, tag).isNotEmpty) ...[
                const SizedBox(height: 6),
                Text(pickName(d.dormitoryDescription, tag)),
              ],
            ]),
          ),
          const SizedBox(height: 8),
          ChunkyButton(
            label: isTarget ? l.removeFromDreams : l.addToDreams,
            loading: _saving,
            tone: isTarget ? ChunkyTone.white : ChunkyTone.blue,
            onPressed: () => _toggleDream(lyceumId, dreams),
          ),
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
