"""Разбор главной страницы atu.edu.az: новости (/xeber/ID) и объявления (/elan/ID).

Логика: каждая карточка на странице заканчивается ссылкой «Ətraflı» вида /xeber/<id> или /elan/<id>.
Для каждой такой ссылки берётся фрагмент HTML ПЕРЕД ней (после предыдущей ссылки), и из него
достаются последняя дата (ГГГГ-ММ-ДД) и последний заголовок (<h1..h6>, а если его нет, alt картинки).
Принимаются только ссылки на atu.edu.az.
"""
import html as html_lib
import re
from urllib.parse import urljoin, urlparse

BASE_URL = "https://atu.edu.az/"
ALLOWED_HOSTS = {"atu.edu.az", "www.atu.edu.az"}
KINDS = {"xeber": "news", "elan": "ann", "tedbir": "events"}

_LINK_RE = re.compile(
    r"""<a\b[^>]*?\bhref\s*=\s*["']([^"']*?/(xeber|elan|tedbir)/(\d+))/?["'][^>]*>""",
    re.IGNORECASE | re.DOTALL,
)
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_HEAD_RE = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.IGNORECASE | re.DOTALL)
_ALT_RE = re.compile(r"""<img[^>]*?\balt\s*=\s*["']([^"']+)["']""", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _clean(fragment: str) -> str:
    text = _TAG_RE.sub(" ", fragment)
    text = html_lib.unescape(text).replace("\xa0", " ")
    return " ".join(text.split())


def parse_home(page: str) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {"news": [], "ann": [], "events": []}
    seen: set[tuple[str, str]] = set()
    prev_end = 0
    for match in _LINK_RE.finditer(page):
        chunk = page[prev_end : match.start()]
        prev_end = match.end()

        url = urljoin(BASE_URL, match.group(1))
        if urlparse(url).netloc.lower() not in ALLOWED_HOSTS:
            continue
        kind = KINDS[match.group(2).lower()]
        key = (kind, match.group(3))
        if key in seen:
            continue

        heads = _HEAD_RE.findall(chunk)
        title = _clean(heads[-1]) if heads else ""
        if not title:
            alts = _ALT_RE.findall(chunk)
            title = _clean(alts[-1]) if alts else ""
        if not title:
            continue

        dates = _DATE_RE.findall(chunk)
        seen.add(key)
        result[kind].append({"date": dates[-1] if dates else "", "title": title[:300], "url": url})
    return result
