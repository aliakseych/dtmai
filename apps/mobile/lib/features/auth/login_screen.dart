import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/api/token_storage.dart';
import '../../core/l10n_ext.dart';
import '../../theme/tokens.dart';
import '../../widgets/chunky_button.dart';
import '../../widgets/mascot.dart';
import '../../router.dart';
import '../learn/learn_providers.dart';
import '../profile/profile_providers.dart';
import 'auth_providers.dart';
import 'language_picker.dart';

enum _Step { login, register, verify, forgot, reset }

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _name = TextEditingController();
  final _password = TextEditingController();
  final _code = TextEditingController();
  _Step _step = _Step.login;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _name.dispose();
    _password.dispose();
    _code.dispose();
    super.dispose();
  }

  Future<void> _run(Future<void> Function() job) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await job();
    } catch (e) {
      if (mounted) setState(() => _error = apiErrorMessage(e, context.l10n.errorGeneric));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Signs in with a real account. A guest's progress is merged into it afterwards.
  Future<void> _finish(TokenPair pair) async {
    final storage = ref.read(tokenStorageProvider);
    final previous = await storage.read();
    final auth = ref.read(authProvider.notifier);
    final wasGuest = ref.read(authProvider) == AuthStatus.signedIn && !auth.hadAccount;
    await ref.read(authProvider.notifier).signIn(pair, account: true);
    var mergeFailed = false;
    if (wasGuest && previous != null && previous.access != pair.access) {
      try {
        await ref.read(apiProvider).mergeGuest(previous.access);
      } catch (_) {
        mergeFailed = true;
      }
    }
    ref.invalidate(meProvider);
    ref.invalidate(statsProvider);
    ref.invalidate(billingProvider);
    ref.invalidate(friendsProvider);
    ref.invalidate(currentLanguageProvider);
    ref.invalidate(currentSubjectIdProvider);
    ref.invalidate(pathProvider);
    if (!mounted) return;
    if (mergeFailed) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(context.l10n.mergeFailed)));
    }
    context.go('/learn');
  }

  Future<void> _login() => _run(() async {
        await _finish(await ref.read(apiProvider).login(_email.text.trim(), _password.text));
      });

  Future<void> _register() => _run(() async {
        final tag = context.localeTag;
        await ref.read(apiProvider).register(
              email: _email.text.trim(),
              name: _name.text.trim(),
              password: _password.text,
              locale: tag,
            );
        if (mounted) setState(() => _step = _Step.verify);
      });

  Future<void> _verify() => _run(() async {
        await _finish(await ref.read(apiProvider).verifyEmail(_email.text.trim(), _code.text.trim()));
      });

  Future<void> _resend() => _run(() => ref.read(apiProvider).resendCode(_email.text.trim()));

  Future<void> _forgot() => _run(() async {
        await ref.read(apiProvider).forgotPassword(_email.text.trim());
        if (mounted) setState(() => _step = _Step.reset);
      });

  Future<void> _reset() async {
    final l = context.l10n;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final pair = await ref.read(apiProvider).resetPassword(_email.text.trim(), _code.text.trim(), _password.text);
      await _finish(pair);
    } on DioException catch (e) {
      final s = e.response?.statusCode;
      if (mounted) setState(() => _error = s == 401 ? l.invalidCode : (s == 422 ? l.weakPassword : apiErrorMessage(e, l.errorGeneric)));
    } catch (e) {
      if (mounted) setState(() => _error = apiErrorMessage(e, l.errorGeneric));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _notNow() async {
    if (ref.read(authProvider) != AuthStatus.signedIn) {
      // Expired real account: continue with a fresh guest.
      await ref.read(authProvider.notifier).continueAsGuest();
      await ref.read(guestBootstrapProvider.notifier).run();
      if (!mounted || ref.read(authProvider) != AuthStatus.signedIn) return;
    }
    context.go('/learn');
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final verifying = _step == _Step.verify;
    final forgot = _step == _Step.forgot;
    final resetting = _step == _Step.reset;
    final registering = _step == _Step.register;
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const Align(alignment: Alignment.centerRight, child: LanguagePicker()),
            const Center(child: Mascot(pose: MascotPose.wave, size: 140)),
            const SizedBox(height: 8),
            Text(
              registering ? l.signUp : (forgot || resetting ? l.forgotPassword : l.signIn),
              style: Theme.of(context).textTheme.headlineMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            if (resetting) ...[
              Text(l.resetPrompt, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              TextField(
                controller: _code,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration: InputDecoration(hintText: l.code, counterText: ''),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _password,
                obscureText: true,
                autofillHints: const [AutofillHints.newPassword],
                decoration: InputDecoration(hintText: l.newPassword),
              ),
            ] else if (verifying) ...[
              Text(l.verifyPrompt, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              TextField(
                controller: _code,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration: InputDecoration(hintText: l.code, counterText: ''),
              ),
            ] else ...[
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                decoration: InputDecoration(hintText: l.email),
              ),
              if (registering) ...[
                const SizedBox(height: 12),
                TextField(
                  controller: _name,
                  autofillHints: const [AutofillHints.name],
                  decoration: InputDecoration(hintText: l.nameLabel),
                ),
              ],
              if (!forgot) ...[
                const SizedBox(height: 12),
                TextField(
                  controller: _password,
                  obscureText: true,
                  autofillHints: [registering ? AutofillHints.newPassword : AutofillHints.password],
                  decoration: InputDecoration(hintText: l.password),
                ),
              ],
            ],
            if (_error != null) ...[
              const SizedBox(height: 12),
              Semantics(liveRegion: true, child: Text(_error!, style: const TextStyle(color: Tokens.red))),
            ],
            const SizedBox(height: 16),
            ChunkyButton(
              label: resetting ? l.resetPassword : (forgot ? l.sendCode : (verifying ? l.verify : (registering ? l.signUp : l.signIn))),
              loading: _busy,
              onPressed: resetting ? _reset : (forgot ? _forgot : (verifying ? _verify : (registering ? _register : _login))),
            ),
            const SizedBox(height: 12),
            if (verifying)
              TextButton(onPressed: _busy ? null : _resend, child: Text(l.resendCode))
            else
              TextButton(
                onPressed: _busy
                    ? null
                    : () => setState(() {
                          _error = null;
                          _step = (registering || forgot || resetting) ? _Step.login : _Step.register;
                        }),
                child: Text((forgot || resetting) ? l.signIn : (registering ? l.haveAccount : l.noAccount)),
              ),
            if (_step == _Step.login)
              TextButton(
                onPressed: _busy ? null : () => setState(() {
                      _error = null;
                      _step = _Step.forgot;
                    }),
                child: Text(l.forgotPassword),
              ),
            TextButton(onPressed: _busy ? null : _notNow, child: Text(l.notNow)),
          ],
        ),
      ),
    );
  }
}
