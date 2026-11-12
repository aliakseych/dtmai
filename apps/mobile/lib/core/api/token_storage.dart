import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class TokenPair {
  const TokenPair(this.access, this.refresh);
  final String access;
  final String refresh;
}

class TokenStorage {
  TokenStorage([FlutterSecureStorage? s]) : _s = s ?? const FlutterSecureStorage();
  final FlutterSecureStorage _s;

  static const _a = 'access_token';
  static const _r = 'refresh_token';
  static const _l = 'locale';

  Future<TokenPair?> read() async {
    final a = await _s.read(key: _a);
    final r = await _s.read(key: _r);
    if (a == null || r == null) return null;
    return TokenPair(a, r);
  }

  Future<void> write(TokenPair p) async {
    await _s.write(key: _a, value: p.access);
    await _s.write(key: _r, value: p.refresh);
  }

  Future<void> clear() async {
    await _s.delete(key: _a);
    await _s.delete(key: _r);
  }

  Future<String?> readLocale() => _s.read(key: _l);
  Future<void> writeLocale(String tag) => _s.write(key: _l, value: tag);

  /// True while the stored identity is a real (email/Telegram) account, so an
  /// expired session sends the user to sign-in instead of silently creating a new guest.
  Future<bool> readHadAccount() async => await _s.read(key: 'had_account') == '1';
  Future<void> writeHadAccount(bool v) => _s.write(key: 'had_account', value: v ? '1' : '0');

  Future<bool> readOnboardingSkipped() async => await _s.read(key: 'onboarding_skipped') == '1';
  Future<void> writeOnboardingSkipped(bool v) => _s.write(key: 'onboarding_skipped', value: v ? '1' : '0');
}

final tokenStorageProvider = Provider<TokenStorage>((_) => TokenStorage());
