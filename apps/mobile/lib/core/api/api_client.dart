import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../config.dart';
import '../locale_controller.dart';
import 'token_storage.dart';

/// Invoked when the refresh token is rejected; the auth layer signs the user out.
typedef SessionExpired = void Function();

/// Adds the bearer token and retries once on 401 after `POST /v1/identity/refresh`.
class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor(this._storage, this._dio, this._onExpired)
      : _refreshDio = Dio(BaseOptions(baseUrl: Config.apiUrl));

  final TokenStorage _storage;
  final Dio _dio;
  final Dio _refreshDio;
  final SessionExpired _onExpired;

  static const _retriedKey = 'auth_retried';

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final t = await _storage.read();
    if (t != null) options.headers['Authorization'] = 'Bearer ${t.access}';
    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    final req = err.requestOptions;
    final isIdentity = req.path.startsWith('/v1/identity/');
    if (err.response?.statusCode != 401 || req.extra[_retriedKey] == true || isIdentity) {
      return handler.next(err);
    }
    final t = await _storage.read();
    if (t == null) return handler.next(err);
    try {
      final res = await _refreshDio.post<Map<String, dynamic>>(
        '/v1/identity/refresh',
        data: {'refresh_token': t.refresh},
      );
      final data = res.data!;
      final pair = TokenPair(data['access_token'] as String, data['refresh_token'] as String);
      await _storage.write(pair);
      req.headers['Authorization'] = 'Bearer ${pair.access}';
      req.extra[_retriedKey] = true;
      handler.resolve(await _dio.fetch<dynamic>(req));
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403 || status == 422) {
        await _storage.clear();
        _onExpired();
      }
      handler.next(err);
    }
  }
}

/// Sends the UI locale (uz-Latn, uz-Cyrl, ru, en) on every request.
class LocaleInterceptor extends Interceptor {
  LocaleInterceptor(this._tag);
  final String Function() _tag;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['Accept-Language'] = _tag();
    handler.next(options);
  }
}

/// Holder so the interceptor can notify the auth controller without a provider cycle.
class SessionExpiredBus {
  SessionExpired? callback;
}

final sessionExpiredBusProvider = Provider<SessionExpiredBus>((_) => SessionExpiredBus());

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: Config.apiUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 30),
    contentType: Headers.jsonContentType,
  ));
  dio.interceptors.addAll([
    LocaleInterceptor(() => AppLocales.toTag(ref.read(localeProvider))),
    AuthInterceptor(
      ref.read(tokenStorageProvider),
      dio,
      () => ref.read(sessionExpiredBusProvider).callback?.call(),
    ),
  ]);
  return dio;
});

/// Human-readable detail from RFC 7807 problem bodies (`detail`, `title`).
String apiErrorMessage(Object e, String fallback) {
  if (e is DioException) {
    final d = e.response?.data;
    if (d is Map) {
      if (d['detail'] is String && (d['detail'] as String).isNotEmpty) return d['detail'] as String;
      if (d['title'] is String) return d['title'] as String;
    }
  }
  return fallback;
}

/// Machine-readable problem `code` (e.g. `no_hearts`).
String? apiErrorCode(Object e) {
  if (e is DioException) {
    final d = e.response?.data;
    if (d is Map && d['code'] is String) return d['code'] as String;
  }
  return null;
}

int? apiStatus(Object e) => e is DioException ? e.response?.statusCode : null;

/// 409 `no_hearts` from the start endpoints.
bool isNoHearts(Object e) => apiStatus(e) == 409 && apiErrorCode(e) == 'no_hearts';
