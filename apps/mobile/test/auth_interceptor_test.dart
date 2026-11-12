import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:dtmai/core/api/api_client.dart';
import 'package:dtmai/core/api/token_storage.dart';
import 'package:flutter_test/flutter_test.dart';

class _MemStorage extends TokenStorage {
  _MemStorage(this.pair);
  TokenPair? pair;

  @override
  Future<TokenPair?> read() async => pair;
  @override
  Future<void> write(TokenPair p) async => pair = p;
  @override
  Future<void> clear() async => pair = null;
}

class _Adapter implements HttpClientAdapter {
  _Adapter(this.handler);
  final ResponseBody Function(RequestOptions o) handler;
  final calls = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(RequestOptions o, Stream<Uint8List>? s, Future<void>? c) async {
    calls.add(o);
    return handler(o);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody _json(int status, Object body) => ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );

Dio _dio(_Adapter a) => Dio(BaseOptions(baseUrl: 'http://t', validateStatus: (s) => s != null && s < 400))
  ..httpClientAdapter = a;

void main() {
  test('refreshes on 401 and retries with the new token', () async {
    final storage = _MemStorage(TokenPair('old', 'r1'));
    final refresh = _Adapter((_) => _json(200, {'access_token': 'new', 'refresh_token': 'r2'}));
    final retry = _Adapter((o) => o.headers['Authorization'] == 'Bearer new' ? _json(200, {'ok': true}) : _json(401, {}));
    var expired = 0;
    final app = _dio(_Adapter((o) => _json(401, {})));
    app.interceptors.add(AuthInterceptor(storage, () => expired++, refreshDio: _dio(refresh), retryDio: _dio(retry)));

    final res = await app.get<dynamic>('/v1/x');
    expect(res.data, {'ok': true});
    expect(storage.pair!.access, 'new');
    expect(expired, 0);
  });

  test('skips refresh when stored token already differs', () async {
    final storage = _MemStorage(TokenPair('stale', 'r1'));
    final refresh = _Adapter((_) => _json(500, {}));
    final retry = _Adapter((_) => _json(200, {'ok': true}));
    // Another request refreshes the pair while this one is in flight.
    final app = _dio(_Adapter((_) {
      storage.pair = TokenPair('fresh', 'r2');
      return _json(401, {});
    }));
    app.interceptors.add(AuthInterceptor(storage, () {}, refreshDio: _dio(refresh), retryDio: _dio(retry)));

    final res = await app.get<dynamic>('/v1/x');
    expect(res.statusCode, 200);
    expect(refresh.calls, isEmpty);
    expect(retry.calls.single.headers['Authorization'], 'Bearer fresh');
  });

  test('refresh rejection clears tokens and signs out', () async {
    final storage = _MemStorage(TokenPair('old', 'r1'));
    final refresh = _Adapter((_) => _json(401, {}));
    var expired = 0;
    final app = _dio(_Adapter((_) => _json(401, {})));
    app.interceptors.add(AuthInterceptor(storage, () => expired++, refreshDio: _dio(refresh), retryDio: _dio(_Adapter((_) => _json(200, {})))));

    await expectLater(app.get<dynamic>('/v1/x'), throwsA(isA<DioException>()));
    expect(storage.pair, isNull);
    expect(expired, 1);
  });

  test('retry failure keeps session and surfaces the retry error', () async {
    final storage = _MemStorage(TokenPair('old', 'r1'));
    final refresh = _Adapter((_) => _json(200, {'access_token': 'new', 'refresh_token': 'r2'}));
    final retry = _Adapter((_) => _json(403, {'code': 'forbidden'}));
    var expired = 0;
    final app = _dio(_Adapter((_) => _json(401, {})));
    app.interceptors.add(AuthInterceptor(storage, () => expired++, refreshDio: _dio(refresh), retryDio: _dio(retry)));

    await expectLater(
      app.get<dynamic>('/v1/x'),
      throwsA(isA<DioException>().having((e) => e.response?.statusCode, 'status', 403)),
    );
    expect(storage.pair!.access, 'new');
    expect(expired, 0);
  });
}
