import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:go_router/go_router.dart';

import '../core/api/api_client.dart';
import '../core/l10n_ext.dart';
import 'chunky_button.dart';
import 'mascot.dart';

/// Mascot + message (+ optional action) used for empty / error / loading / guest states.
class MascotMessage extends StatelessWidget {
  const MascotMessage({super.key, required this.pose, required this.message, this.action, this.size = 120});
  final MascotPose pose;
  final String message;
  final Widget? action;
  final double size;

  @override
  Widget build(BuildContext context) => Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Mascot(pose: pose, size: size),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
              if (action != null) ...[const SizedBox(height: 16), action!],
            ],
          ),
        ),
      );
}

/// Loading / error(+retry) / empty / data wrapper for providers.
class AsyncView<T> extends StatelessWidget {
  const AsyncView({
    super.key,
    required this.value,
    required this.builder,
    this.onRetry,
    this.isEmpty,
    this.emptyMessage,
  });

  final AsyncValue<T> value;
  final Widget Function(T data) builder;
  final VoidCallback? onRetry;
  final bool Function(T data)? isEmpty;
  final String? emptyMessage;

  @override
  Widget build(BuildContext context) {
    return value.when(
      loading: () => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Mascot(pose: MascotPose.thinking, size: 96),
            SizedBox(height: 12),
            CircularProgressIndicator(),
          ],
        ),
      ),
      error: (e, _) => MascotMessage(
        pose: MascotPose.sad,
        message: apiStatus(e) == 401 ? context.l10n.sessionExpired : apiErrorMessage(e, context.l10n.errorGeneric),
        action: apiStatus(e) == 401
            ? ChunkyButton(label: context.l10n.signIn, expand: false, onPressed: () => context.go('/login'))
            : onRetry == null
                ? null
                : ChunkyButton(label: context.l10n.retry, expand: false, tone: ChunkyTone.blue, onPressed: onRetry),
      ),
      data: (d) => isEmpty?.call(d) == true
          ? MascotMessage(pose: MascotPose.sleep, message: emptyMessage ?? context.l10n.empty)
          : builder(d),
    );
  }
}
