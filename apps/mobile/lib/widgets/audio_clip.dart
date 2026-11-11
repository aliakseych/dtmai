import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';

import '../core/l10n_ext.dart';
import '../theme/tokens.dart';

/// Play/pause control for a question's audio clip (listening tasks).
class AudioClip extends StatefulWidget {
  const AudioClip({super.key, required this.url, this.label});
  final String url;
  final String? label;

  @override
  State<AudioClip> createState() => _AudioClipState();
}

class _AudioClipState extends State<AudioClip> {
  final AudioPlayer _player = AudioPlayer();
  bool _failed = false;
  bool _loaded = false;

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  Future<void> _toggle() async {
    try {
      if (_player.playing) {
        await _player.pause();
        return;
      }
      if (!_loaded) {
        await _player.setUrl(widget.url);
        _loaded = true;
      }
      if (_player.processingState == ProcessingState.completed) await _player.seek(Duration.zero);
      await _player.play();
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Tokens.blueSoft,
        border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
        borderRadius: BorderRadius.circular(Tokens.radius),
      ),
      child: StreamBuilder<PlayerState>(
        stream: _player.playerStateStream,
        builder: (context, snap) {
          final st = snap.data;
          final playing = (st?.playing ?? false) && st?.processingState != ProcessingState.completed;
          final loading = st?.processingState == ProcessingState.loading || st?.processingState == ProcessingState.buffering;
          return Row(children: [
            IconButton(
              tooltip: playing ? l.pauseAudio : l.playAudio,
              onPressed: _toggle,
              icon: loading
                  ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 3))
                  : Icon(playing ? Icons.pause_circle_filled_rounded : Icons.play_circle_fill_rounded, color: Tokens.blue, size: 36),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                _failed ? l.audioFailed : (widget.label ?? l.listen),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontWeight: FontWeight.w700, color: _failed ? Tokens.redEdge : Tokens.blueText),
              ),
            ),
          ]);
        },
      ),
    );
  }
}
