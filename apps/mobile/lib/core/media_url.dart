import 'package:flutter/foundation.dart' show kReleaseMode;

import 'config.dart';

/// Resolves a media key or absolute URL to a safe URL, or null (render nothing).
/// Relative keys are joined to the media base (or API origin). Absolute URLs must be
/// https (http only outside release) and point at the media or API host.
String? resolveMedia(
  String? raw, {
  String mediaBase = Config.mediaUrl,
  String apiBase = Config.apiUrl,
  bool release = kReleaseMode,
}) {
  final value = raw?.trim();
  if (value == null || value.isEmpty) return null;
  final api = Uri.parse(apiBase);
  final media = mediaBase.isEmpty ? api : Uri.parse(mediaBase);
  final abs = Uri.tryParse(value);
  if (abs != null && abs.hasScheme) {
    final ok = abs.scheme == 'https' || (!release && abs.scheme == 'http');
    if (!ok || abs.host.isEmpty) return null;
    return (abs.host == media.host || abs.host == api.host) ? value : null;
  }
  if (value.startsWith('//')) return null;
  final base = (mediaBase.isEmpty ? api.origin : mediaBase).replaceAll(RegExp(r'/+$'), '');
  return '$base/${value.replaceFirst(RegExp(r'^/+'), '')}';
}
