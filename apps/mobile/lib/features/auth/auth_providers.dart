import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/token_storage.dart';

enum AuthStatus { unknown, signedOut, signedIn }

class AuthController extends Notifier<AuthStatus> {
  /// Whether the last signed-in identity was a real account (persisted).
  bool hadAccount = false;

  @override
  AuthStatus build() {
    ref.read(sessionExpiredBusProvider).callback = () => state = AuthStatus.signedOut;
    _restore();
    return AuthStatus.unknown;
  }

  Future<void> _restore() async {
    final storage = ref.read(tokenStorageProvider);
    final t = await storage.read();
    hadAccount = await storage.readHadAccount();
    state = t == null ? AuthStatus.signedOut : AuthStatus.signedIn;
  }

  /// [account] is true for email/Telegram sign-in, false for an anonymous guest.
  Future<void> signIn(TokenPair pair, {required bool account}) async {
    final storage = ref.read(tokenStorageProvider);
    await storage.write(pair);
    await storage.writeHadAccount(account);
    hadAccount = account;
    state = AuthStatus.signedIn;
  }

  /// Drops the remembered account so a fresh guest is created ("Not now" on sign-in).
  Future<void> continueAsGuest() async {
    await ref.read(tokenStorageProvider).writeHadAccount(false);
    hadAccount = false;
  }

  Future<void> signOut() async {
    await ref.read(tokenStorageProvider).clear();
    state = AuthStatus.signedOut;
  }
}

final authProvider = NotifierProvider<AuthController, AuthStatus>(AuthController.new);

/// Whether the user chose "Not now" in onboarding (persisted).
class OnboardingSkipped extends Notifier<bool> {
  @override
  bool build() {
    ref.read(tokenStorageProvider).readOnboardingSkipped().then((v) {
      if (v) state = true;
    });
    return false;
  }

  Future<void> skip() async {
    state = true;
    await ref.read(tokenStorageProvider).writeOnboardingSkipped(true);
  }
}

final onboardingSkippedProvider = NotifierProvider<OnboardingSkipped, bool>(OnboardingSkipped.new);
