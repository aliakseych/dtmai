from app.shared.media import sniff_media

WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 "


def test_sniff_known_types() -> None:
    assert sniff_media(b"\x89PNG\r\n\x1a\n....") == ("image/png", ".png")
    assert sniff_media(b"\xff\xd8\xff\xe0abc") == ("image/jpeg", ".jpg")
    assert sniff_media(b"GIF89a..") == ("image/gif", ".gif")
    assert sniff_media(b"%PDF-1.7") == ("application/pdf", ".pdf")
    assert sniff_media(WEBP) == ("image/webp", ".webp")


def test_sniff_rejects_svg_html_and_empty() -> None:
    assert sniff_media(b'<svg xmlns="http://www.w3.org/2000/svg"/>') is None
    assert sniff_media(b"<html><script>alert(1)</script>") is None
    assert sniff_media(b"RIFF\x00\x00\x00\x00WAVEfmt ") is None
    assert sniff_media(b"") is None
