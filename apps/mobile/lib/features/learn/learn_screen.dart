import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../../widgets/mascot.dart';
import '../../widgets/path_node.dart';
import '../../widgets/stat_chips.dart';
import '../auth/auth_providers.dart';
import '../lyceums/lyceum_providers.dart';
import '../profile/profile_providers.dart';
import 'learn_providers.dart';

class LearnScreen extends ConsumerWidget {
  const LearnScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final stats = ref.watch(statsProvider).value;
    final path = ref.watch(pathProvider);
    final subjectId = ref.watch(currentSubjectIdProvider).value;
    final placement = subjectId == null ? null : ref.watch(placementProvider(subjectId)).value;
    final signedIn = ref.watch(authProvider) == AuthStatus.signedIn;
    return Scaffold(
      appBar: AppBar(
        title: Text(l.learn),
        actions: [
          IconButton(icon: const Icon(Icons.flag_rounded), tooltip: l.quests, onPressed: () => context.push('/quests')),
          IconButton(icon: const Icon(Icons.school_rounded), tooltip: l.lyceums, onPressed: () => context.push('/lyceums')),
          if (stats != null) StatChips(stats: stats),
        ],
      ),
      body: Column(
        children: [
          const _SubjectTabs(),
          const _LanguageTabs(),
          if (signedIn && subjectId != null && ref.watch(placementProvider(subjectId)).hasValue && placement == null)
            _PlacementBanner(subjectId: subjectId),
          Expanded(
            child: AsyncView<LearnerPath?>(
              value: path,
              onRetry: () => ref.invalidate(pathProvider),
              isEmpty: (p) => p == null || p.units.isEmpty,
              emptyMessage: l.noPath,
              builder: (p) => RefreshIndicator(
                onRefresh: () async {
                  ref.invalidate(pathProvider);
                  ref.invalidate(statsProvider);
                },
                child: ListView.builder(
                  padding: const EdgeInsets.only(bottom: 32),
                  itemCount: p!.units.length,
                  itemBuilder: (_, i) => _UnitSection(unit: p.units[i], index: i),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SubjectTabs extends ConsumerWidget {
  const _SubjectTabs();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final subjects = ref.watch(subjectsProvider).value ?? const <Subject>[];
    final current = ref.watch(currentSubjectIdProvider).value;
    final tag = context.localeTag;
    if (subjects.isEmpty) return const SizedBox.shrink();
    return SizedBox(
      height: 52,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        children: [
          for (final s in subjects)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(pickName(s.names, tag)),
                selected: s.id == current,
                selectedColor: Tokens.blueSoft,
                labelStyle: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: s.id == current ? Tokens.blueText : Tokens.text,
                ),
                onSelected: (_) => ref.read(selectedSubjectProvider.notifier).set(s.id),
              ),
            ),
        ],
      ),
    );
  }
}

/// Education-language switcher (profile for signed-in users, local choice for guests).
class _LanguageTabs extends ConsumerWidget {
  const _LanguageTabs();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final langs = ref.watch(languagesProvider).value ?? const <EduLanguage>[];
    final current = ref.watch(currentLanguageProvider).value;
    final tag = context.localeTag;
    if (langs.length < 2) return const SizedBox.shrink();
    return SizedBox(
      height: 44,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          for (final lang in langs)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(pickName(lang.names, tag)),
                selected: lang.id == current?.id,
                selectedColor: Tokens.greenSoft,
                labelStyle: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: lang.id == current?.id ? Tokens.greenText : Tokens.text,
                ),
                onSelected: (_) async {
                  final signedIn = ref.read(authProvider) == AuthStatus.signedIn;
                  if (signedIn) {
                    try {
                      await ref.read(apiProvider).patchMe(educationLanguageId: lang.id);
                      ref.invalidate(meProvider);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context)
                            .showSnackBar(SnackBar(content: Text(apiErrorMessage(e, context.l10n.errorGeneric))));
                      }
                    }
                  } else {
                    ref.read(guestLanguageProvider.notifier).set(lang.id);
                  }
                },
              ),
            ),
        ],
      ),
    );
  }
}

class _PlacementBanner extends ConsumerStatefulWidget {
  const _PlacementBanner({required this.subjectId});
  final String subjectId;

  @override
  ConsumerState<_PlacementBanner> createState() => _PlacementBannerState();
}

class _PlacementBannerState extends ConsumerState<_PlacementBanner> {
  bool _busy = false;

  Future<void> _skip() async {
    setState(() => _busy = true);
    try {
      await ref.read(apiProvider).skipPlacement(widget.subjectId);
      ref.invalidate(placementProvider(widget.subjectId));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(apiErrorMessage(e, context.l10n.errorGeneric))));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return Container(
      margin: const EdgeInsets.fromLTRB(12, 4, 12, 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Tokens.blueSoft,
        border: Border.all(color: Tokens.blue, width: Tokens.borderWidth),
        borderRadius: BorderRadius.circular(Tokens.radius),
      ),
      child: Row(
        children: [
          const Mascot(pose: MascotPose.thinking, size: 56),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l.placementBannerTitle, style: const TextStyle(fontWeight: FontWeight.w800, color: Tokens.blueText)),
                Text(l.placementBannerBody, style: const TextStyle(fontSize: 13)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: ChunkyButton(
                        label: l.startPlacement,
                        tone: ChunkyTone.blue,
                        onPressed: () => context.push('/session/placement/${widget.subjectId}'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    TextButton(onPressed: _busy ? null : _skip, child: Text(l.skipPlacement)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

const _offsets = [0.0, 0.5, 0.8, 0.5, 0.0, -0.5, -0.8, -0.5];

class _UnitSection extends StatelessWidget {
  const _UnitSection({required this.unit, required this.index});
  final PathUnit unit;
  final int index;

  NodeState _state(PathLesson lesson, bool isFirstOpen) {
    if (lesson.progress.locked || unit.progress.locked) return NodeState.locked;
    if (lesson.progress.done) return NodeState.done;
    return isFirstOpen ? NodeState.current : NodeState.open;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: double.infinity,
          margin: const EdgeInsets.fromLTRB(16, 16, 16, 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: Tokens.greenEdge, borderRadius: BorderRadius.circular(Tokens.radius)),
          child: Text(
            unit.title,
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16),
          ),
        ),
        for (var i = 0; i < unit.lessons.length; i++)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Align(
              alignment: Alignment(_offsets[i % _offsets.length], 0),
              child: PathNode(
                lesson: unit.lessons[i],
                state: _state(
                  unit.lessons[i],
                  unit.lessons.indexWhere((x) => !x.progress.done && !x.progress.locked) == i,
                ),
                onTap: () => context.push('/session/lesson/${unit.lessons[i].id}'),
              ),
            ),
          ),
      ],
    );
  }
}
