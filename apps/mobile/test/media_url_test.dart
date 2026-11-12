import 'package:flutter_test/flutter_test.dart';
import 'package:dtmai/core/media_url.dart';

void main() {
  const api = 'https://api.dtm-ai.uz';
  const media = 'https://media.dtm-ai.uz/';
  String? r(String? v, {bool release = true, String m = media}) =>
      resolveMedia(v, mediaBase: m, apiBase: api, release: release);

  test('relative key uses media base', () {
    expect(r('/img/a.png'), 'https://media.dtm-ai.uz/img/a.png');
  });
  test('relative key falls back to api origin', () {
    expect(r('img/a.png', m: ''), 'https://api.dtm-ai.uz/img/a.png');
  });
  test('allowed absolute hosts', () {
    expect(r('https://media.dtm-ai.uz/x.png'), 'https://media.dtm-ai.uz/x.png');
    expect(r('https://api.dtm-ai.uz/x.png'), 'https://api.dtm-ai.uz/x.png');
  });
  test('foreign host rejected', () {
    expect(r('https://evil.example/x.png'), isNull);
    expect(r('//evil.example/x.png'), isNull);
  });
  test('http only outside release', () {
    expect(r('http://media.dtm-ai.uz/x.png'), isNull);
    expect(r('http://media.dtm-ai.uz/x.png', release: false), 'http://media.dtm-ai.uz/x.png');
  });
  test('null/empty', () {
    expect(r(null), isNull);
    expect(r(' '), isNull);
  });
}
