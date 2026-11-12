import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/l10n_ext.dart';
import '../../core/locale_controller.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../../widgets/mascot.dart';
import '../../widgets/priority_picker.dart';
import '../auth/auth_providers.dart';
import '../learn/learn_providers.dart';
import '../lyceums/lyceum_providers.dart';
import '../profile/profile_providers.dart';

const _goals = [10, 20, 30, 50];

/// Locale, subject, education language, target lyceum, daily goal; then an optional placement test.
class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  List<String> _dreams = [];
  String? _city; // null = any city
  final Set<String> _subjects = {};
  String? _languageId;
  int _goal = 30;
  bool _busy = false;
  String? _error;

  Future<void> _save({required bool placement}) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final api = ref.read(apiProvider);
      final chosen = _subjects.isNotEmpty ? _subjects.first : null;
      if (chosen != null) ref.read(selectedSubjectProvider.notifier).set(chosen);
      final subjectId = chosen ?? await ref.read(currentSubjectIdProvider.future);
      await api.patchMe(
        locale: AppLocales.toTag(ref.read(localeProvider)),
        dreamLyceumIds: _dreams,
        subjectIds: _subjects.toList(),
        educationLanguageId: _languageId,
        city: _city,
        clearCity: _city == null,
      );
      await api.setDailyGoal(_goal);
      if (!placement && subjectId != null) await api.skipPlacement(subjectId);
      ref.invalidate(statsProvider);
      ref.invalidate(pathProvider);
      ref.invalidate(meProvider);
      await ref.read(meProvider.future);
      if (!mounted) return;
      context.go(placement && subjectId != null ? '/session/placement/$subjectId' : '/learn');
    } catch (e) {
      if (mounted) setState(() => _error = apiErrorMessage(e, context.l10n.errorGeneric));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _notNow() async {
    await ref.read(onboardingSkippedProvider.notifier).skip();
    if (mounted) context.go('/learn');
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final tag = context.localeTag;
    final lyceums = ref.watch(lyceumsProvider);
    final cities = ref.watch(citiesProvider);
    final languages = ref.watch(languagesProvider);
    final subjects = ref.watch(subjectsProvider);
    final locale = ref.watch(localeProvider);
    final titleStyle = Theme.of(context).textTheme.titleMedium;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const Center(child: Mascot(pose: MascotPose.top, size: 120)),
            Text(l.onboardingTitle, style: Theme.of(context).textTheme.headlineMedium, textAlign: TextAlign.center),
            const SizedBox(height: 24),
            Text(l.language, style: titleStyle),
            const SizedBox(height: 8),
            Wrap(spacing: 8, children: [
              for (final x in AppLocales.all)
                ChoiceChip(
                  label: Text(AppLocales.label(x)),
                  selected: x == locale,
                  onSelected: (_) => ref.read(localeProvider.notifier).set(x),
                ),
            ]),
            const SizedBox(height: 16),
            Text(l.chooseSubjects, style: titleStyle),
            const SizedBox(height: 8),
            AsyncView<List<Subject>>(
              value: subjects,
              onRetry: () => ref.invalidate(subjectsProvider),
              builder: (list) => Wrap(spacing: 8, children: [
                for (final s in list)
                  ChoiceChip(
                    label: Text(pickName(s.names, tag)),
                    selected: _subjects.contains(s.id),
                    onSelected: (v) => setState(() => v ? _subjects.add(s.id) : _subjects.remove(s.id)),
                  ),
              ]),
            ),
            const SizedBox(height: 16),
            Text(l.chooseLanguage, style: titleStyle),
            const SizedBox(height: 8),
            AsyncView<List<EduLanguage>>(
              value: languages,
              onRetry: () => ref.invalidate(languagesProvider),
              builder: (list) => Wrap(spacing: 8, children: [
                for (final x in list)
                  ChoiceChip(
                    label: Text(pickName(x.names, tag)),
                    selected: _languageId == x.id,
                    onSelected: (_) => setState(() => _languageId = x.id),
                  ),
              ]),
            ),
            const SizedBox(height: 16),
            Text(l.chooseCity, style: titleStyle),
            const SizedBox(height: 4),
            Text(l.cityHint, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Tokens.textMuted)),
            const SizedBox(height: 8),
            AsyncView<List<City>>(
              value: cities,
              onRetry: () => ref.invalidate(citiesProvider),
              builder: (list) => ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 180),
                child: SingleChildScrollView(
                  child: Wrap(spacing: 8, children: [
                ChoiceChip(
                  label: Text(l.anyCity),
                  selected: _city == null,
                  onSelected: (_) => setState(() => _city = null),
                ),
                for (final c in list)
                  ChoiceChip(
                    label: Text(pickName(c.names, tag)),
                    selected: _city == c.code,
                    onSelected: (_) => setState(() => _city = c.code),
                  ),
              ]),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(l.dreamLyceums, style: titleStyle),
            const SizedBox(height: 8),
            AsyncView<List<Lyceum>>(
              value: lyceums,
              onRetry: () => ref.invalidate(lyceumsProvider),
              builder: (all) {
                final names = {for (final x in all) x.id: pickName(x.names, tag)};
                final list = (_city == null ? all : all.where((x) => x.city == _city).toList())
                    .where((x) => !_dreams.contains(x.id))
                    .toList();
                return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  PriorityPicker(ids: _dreams, nameOf: (id) => names[id] ?? '', onChanged: (v) => setState(() => _dreams = v)),
                  if (_dreams.length < maxDreamLyceums) ...[
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      key: ValueKey('${_city}_${_dreams.length}'),
                      initialValue: null,
                      isExpanded: true,
                      hint: Text(l.addLyceum),
                      menuMaxHeight: 320,
                      items: [
                        for (final x in list)
                          DropdownMenuItem(value: x.id, child: Text(pickName(x.names, tag), overflow: TextOverflow.ellipsis)),
                      ],
                      onChanged: (v) => setState(() {
                        if (v != null && _dreams.length < maxDreamLyceums) _dreams = [..._dreams, v];
                      }),
                    ),
                  ],
                ]);
              },
            ),
            const SizedBox(height: 16),
            Text(l.dailyGoal, style: titleStyle),
            const SizedBox(height: 8),
            Wrap(spacing: 8, children: [
              for (final g in _goals)
                ChoiceChip(label: Text('$g ${l.xp}'), selected: _goal == g, onSelected: (_) => setState(() => _goal = g)),
            ]),
            if (_error != null)
              Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
            const SizedBox(height: 24),
            ChunkyButton(
              label: l.startPlacement,
              loading: _busy,
              onPressed: _languageId != null ? () => _save(placement: true) : null,
            ),
            const SizedBox(height: 8),
            TextButton(onPressed: _busy || _languageId == null ? null : () => _save(placement: false), child: Text(l.skipPlacement)),
            TextButton(onPressed: _busy ? null : _notNow, child: Text(l.notNow)),
          ],
        ),
          ),
        ),
      ),
    );
  }
}
