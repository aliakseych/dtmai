import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/l10n_ext.dart';
import '../../core/media_url.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/audio_clip.dart';
import '../../widgets/math_text.dart';
import '../../widgets/option_tile.dart';
import 'session_providers.dart';

class _PassageBlock extends ConsumerWidget {
  const _PassageBlock({required this.id});
  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final p = ref.watch(passageProvider(id));
    return p.when(
      loading: () => const Padding(padding: EdgeInsets.all(8), child: LinearProgressIndicator()),
      error: (_, _) => const SizedBox.shrink(),
      data: (d) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Tokens.blueSoft,
          borderRadius: BorderRadius.circular(Tokens.radius),
          border: Border.all(color: Tokens.border, width: 2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (final m in d.media.where((m) => m.kind == 'image' && resolveMedia(m.url) != null))
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Image.network(resolveMedia(m.url)!, semanticLabel: m.alt, errorBuilder: (_, _, _) => const SizedBox.shrink()),
              ),
            MathText(d.text, style: const TextStyle(fontSize: 16, color: Tokens.text)),
          ],
        ),
      ),
    );
  }
}

/// Whether [answer] is complete enough to submit for [item].
bool isAnswered(Item item, Json? answer) {
  if (answer == null) return false;
  if (item.kind == 'passage_group') {
    final m = (answer['answers'] as Map? ?? const {});
    return item.children.isNotEmpty && item.children.every((c) => m[c.id] != null && isAnswered(c, Map<String, dynamic>.from(m[c.id] as Map)));
  }
  switch (item.kind) {
    case 'single_choice':
      return answer['choice'] != null;
    case 'multi_choice':
      return (answer['choices'] as List? ?? const []).isNotEmpty;
    case 'numeric':
      final v = answer['value'];
      return v != null && '$v'.trim().isNotEmpty;
    case 'short_text':
      return '${answer['text'] ?? ''}'.trim().isNotEmpty;
    case 'matching':
      final pairs = (answer['pairs'] as Map? ?? const {});
      return pairs.length >= item.optionsOf('left').length && pairs.isNotEmpty;
    case 'ordering':
      return (answer['order'] as List? ?? const []).isNotEmpty;
    default:
      return false;
  }
}

String _textOf(List<ChoiceOpt> opts, Object? id) {
  for (final o in opts) {
    if (o.id == '$id') return o.text;
  }
  return '$id';
}

/// Human readable correct answer built from option texts (never raw ids).
String formatCorrect(Item item, Json correct) {
  if (item.kind == 'passage_group') {
    final answers = (correct['answers'] as Map?) ?? const {};
    return [
      for (final c in item.children)
        if (answers[c.id] is Map) formatCorrect(c, Map<String, dynamic>.from(answers[c.id] as Map)),
    ].join('\n');
  }
  switch (item.kind) {
    case 'single_choice':
      return _textOf(item.optionsOf('options'), correct['choice']);
    case 'multi_choice':
      final opts = item.optionsOf('options');
      return ((correct['choices'] as List?) ?? const []).map((id) => _textOf(opts, id)).join(', ');
    case 'numeric':
      return '${correct['value'] ?? ''}';
    case 'short_text':
      final accepted = correct['accepted'];
      if (accepted is List && accepted.isNotEmpty) return '${accepted.first}';
      return '${correct['text'] ?? ''}';
    case 'matching':
      final left = item.optionsOf('left');
      final right = item.optionsOf('right');
      final pairs = (correct['pairs'] as Map?) ?? const {};
      return pairs.entries.map((e) => '${_textOf(left, e.key)} → ${_textOf(right, e.value)}').join('\n');
    case 'ordering':
      final items = item.optionsOf('items');
      return ((correct['order'] as List?) ?? const []).map((id) => _textOf(items, id)).join(' → ');
    default:
      return '';
  }
}

/// Scrollable page for a question (or passage group).
class QuestionView extends StatelessWidget {
  const QuestionView({
    super.key,
    required this.item,
    required this.answer,
    required this.onChanged,
    this.locked = false,
    this.correctResponse,
  });

  final Item item;
  final Json? answer;
  final ValueChanged<Json?> onChanged;
  final bool locked;
  final Json? correctResponse;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          QuestionBody(item: item, answer: answer, onChanged: onChanged, locked: locked, correctResponse: correctResponse),
        ],
      );
}

/// Non-scrolling question content; a `passage_group` renders its children under the passage.
class QuestionBody extends StatefulWidget {
  const QuestionBody({
    super.key,
    required this.item,
    required this.answer,
    required this.onChanged,
    this.locked = false,
    this.correctResponse,
  });

  final Item item;
  final Json? answer;
  final ValueChanged<Json?> onChanged;
  final bool locked;

  /// Set after checking, to highlight the correct option(s).
  final Json? correctResponse;

  @override
  State<QuestionBody> createState() => _QuestionViewState();
}

class _QuestionViewState extends State<QuestionBody> {
  late final TextEditingController _text;
  List<ChoiceOpt> _order = const [];

  Item get item => widget.item;

  @override
  void initState() {
    super.initState();
    final a = widget.answer;
    _text = TextEditingController(text: '${a?['value'] ?? a?['text'] ?? ''}');
    if (item.kind == 'ordering') {
      final saved = (a?['order'] as List?)?.map((e) => '$e').toList();
      final all = item.optionsOf('items');
      if (saved != null && saved.length == all.length) {
        _order = [for (final id in saved) all.firstWhere((o) => o.id == id, orElse: () => all.first)];
      } else {
        // Not an answer until the learner moves something.
        _order = all;
      }
    }
  }

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  Set<String> get _selected {
    final a = widget.answer;
    if (a == null) return {};
    if (a['choice'] != null) return {'${a['choice']}'};
    return ((a['choices'] as List?) ?? const []).map((e) => '$e').toSet();
  }

  Set<String> get _correct {
    final c = widget.correctResponse;
    if (c == null) return {};
    if (c['choice'] != null) return {'${c['choice']}'};
    return ((c['choices'] as List?) ?? const []).map((e) => '$e').toSet();
  }

  OptionStatus _status(String id) {
    final checked = widget.correctResponse != null;
    if (checked && _correct.contains(id)) return OptionStatus.correct;
    if (checked && _selected.contains(id)) return OptionStatus.wrong;
    return _selected.contains(id) ? OptionStatus.selected : OptionStatus.idle;
  }

  void _toggle(String id) {
    if (widget.locked) return;
    if (item.kind == 'multi_choice') {
      final cur = _selected.toList();
      cur.contains(id) ? cur.remove(id) : cur.add(id);
      widget.onChanged(cur.isEmpty ? null : {'choices': cur});
    } else {
      widget.onChanged({'choice': id});
    }
  }

  Widget _choices() {
    final opts = item.optionsOf('options');
    return Column(
      children: [
        for (var i = 0; i < opts.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: OptionTile(
              hotkey: String.fromCharCode(65 + i),
              text: opts[i].text,
              status: _status(opts[i].id),
              onTap: widget.locked ? null : () => _toggle(opts[i].id),
            ),
          ),
      ],
    );
  }

  Widget _input(BuildContext context) {
    final numeric = item.kind == 'numeric';
    return Semantics(
      textField: true,
      label: context.l10n.typeAnswer,
      child: TextField(
        controller: _text,
        enabled: !widget.locked,
        keyboardType: numeric ? const TextInputType.numberWithOptions(decimal: true, signed: true) : TextInputType.text,
        decoration: InputDecoration(hintText: context.l10n.typeAnswer),
        onChanged: (v) {
          final t = v.trim();
          if (t.isEmpty) return widget.onChanged(null);
          if (!numeric) return widget.onChanged({'text': t});
          final norm = t.replaceAll(RegExp(r'\s'), '').replaceAll(',', '.');
          widget.onChanged({'value': num.tryParse(norm) ?? norm});
        },
      ),
    );
  }

  Widget _matching(BuildContext context) {
    final left = item.optionsOf('left');
    final right = item.optionsOf('right');
    final pairs = Map<String, dynamic>.from((widget.answer?['pairs'] as Map?) ?? const {});
    return Column(
      children: [
        for (final lo in left)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                Expanded(child: MathText(lo.text, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
                const SizedBox(width: 12),
                Expanded(
                  child: Semantics(
                    label: lo.text,
                    child: DropdownButtonFormField<String>(
                      isExpanded: true,
                      value: pairs[lo.id] as String?,
                      items: [for (final r in right) DropdownMenuItem(value: r.id, child: MathText(r.text))],
                      onChanged: widget.locked
                          ? null
                          : (v) {
                              if (v == null) return;
                              widget.onChanged({'pairs': {...pairs, lo.id: v}});
                            },
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _ordering() {
    return ReorderableListView(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      buildDefaultDragHandles: !widget.locked,
      onReorder: (from, to) {
        if (widget.locked) return;
        setState(() {
          if (to > from) to -= 1;
          _order = List.of(_order)..insert(to, _order.removeAt(from));
        });
        widget.onChanged({'order': _order.map((o) => o.id).toList()});
      },
      children: [
        for (final o in _order)
          Padding(
            key: ValueKey(o.id),
            padding: const EdgeInsets.only(bottom: 8),
            child: Semantics(
              label: o.text,
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
                  borderRadius: BorderRadius.circular(Tokens.radius),
                ),
                child: Row(
                  children: [
                    Expanded(child: MathText(o.text)),
                    const Icon(Icons.drag_handle, color: Tokens.textMuted),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _group(BuildContext context) {
    final answers = Map<String, dynamic>.from((widget.answer?['answers'] as Map?) ?? const {});
    final correct = (widget.correctResponse?['answers'] as Map?) ?? const {};
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        for (final c in item.children) ...[
          QuestionBody(
            key: ValueKey(c.id),
            item: c,
            answer: answers[c.id] == null ? null : Map<String, dynamic>.from(answers[c.id] as Map),
            locked: widget.locked,
            correctResponse: correct[c.id] == null ? null : Map<String, dynamic>.from(correct[c.id] as Map),
            onChanged: (r) {
              final next = {...answers};
              r == null ? next.remove(c.id) : next[c.id] = r;
              widget.onChanged(next.isEmpty ? null : {'answers': next});
            },
          ),
          const SizedBox(height: 24),
        ],
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final img = resolveMedia(item.imageUrl);
    final audio = resolveMedia(item.audioUrl);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (img != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(Tokens.radius),
              child: Image.network(img, errorBuilder: (_, _, _) => const SizedBox.shrink()),
            ),
          ),
        if (item.passageId != null) ...[
          _PassageBlock(id: item.passageId!),
          const SizedBox(height: 12),
        ],
        if (audio != null) ...[
          AudioClip(url: audio, label: item.media.firstWhere((m) => m.kind == 'audio').alt),
          const SizedBox(height: 12),
        ],
        MathText(item.stem, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: Tokens.text)),
        const SizedBox(height: 20),
        switch (item.kind) {
          'passage_group' => _group(context),
          'single_choice' || 'multi_choice' => _choices(),
          'numeric' || 'short_text' => _input(context),
          'matching' => _matching(context),
          'ordering' => _ordering(),
          _ => const SizedBox.shrink(),
        },
      ],
    );
  }
}
