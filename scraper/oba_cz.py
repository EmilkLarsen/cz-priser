"""Oba.cz (CZK, Czech Republic) — hagebau group; robots.txt lacks a sitemap
header but /sitemap.xml serves the index. Product URLs /p/<id>; itemprop price."""
import re
from common import get, sane_price, valid_ean, write_jsonl, scrape_urls

BASE = "https://www.oba.cz"
OUT = "data/latest/oba_cz.jsonl"


def fetch_url_list(limit=None):
    idx = get(f"{BASE}/sitemap.xml")
    files = re.findall(r"<loc>([^<]+)</loc>", idx)
    urls = []
    for f in files:
        try:
            xml = get(f)
        except Exception:
            continue
        us = re.findall(r"<loc>(https://www\.oba\.cz/[^<]+/p/\d+)</loc>", xml)
        urls.extend(us)
        if limit and len(urls) >= limit:
            break
    return urls[:limit] if limit else urls


def handle(u, html):
    m = re.search(r'itemprop="price" content="([0-9.]+)"', html)
    if not m:
        return []
    p = sane_price(float(m.group(1)))
    if not p:
        return []
    sk = re.search(r'itemprop="sku" content="([^"]+)"', html)
    t = re.search(r"<title[^>]*>([^<]+)</title>", html)
    name = (t.group(1).split("|")[0].strip() if t else u.rsplit("/", 1)[-1])
    return [{
        "chain": "oba_cz",
        "country": "cz",
        "currency": "CZK",
        "sku": sk.group(1) if sk else None,
        "ean": None,
        "name": name,
        "url": u,
        "price": p,
        "in_stock": None,
        "image": None,
    }]


def scrape(limit=None):
    return scrape_urls(fetch_url_list(limit), handle)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = scrape(lim)
    write_jsonl(OUT, rows)
    print("oba_cz: %d products -> %s" % (len(rows), OUT))
