"""Bauhaus.cz (CZK, Czech Republic) — replaces the dead oba.cz splash site.

sitemap.xml (50k URLs) + sitemap-1.xml; product pages end in a 7-9 digit id
(e.g. -26078146) while categories carry 6-digit ids (-243812). Verified
2026-09-24: itemprop="price" content="1090.00" is the incl-VAT CZK price
(the JSON "price" key is ex-VAT — do not use), og:image present.
"""
import re
from common import get, sane_price, write_jsonl, scrape_urls, scrape_with_checkpoint

BASE = "https://www.bauhaus.cz"
OUT = "data/latest/bauhaus_cz.jsonl"


def fetch_url_list(limit=None):
    urls = []
    seen = set()
    for sm in ("sitemap.xml", "sitemap-1.xml"):
        try:
            xml = get(f"{BASE}/{sm}")
        except Exception:
            continue
        for u in re.findall(r"<loc>([^<]+)</loc>", xml):
            u = u.strip()
            if u in seen or not re.search(r"-\d{7,9}$", u):
                continue
            seen.add(u)
            urls.append(u)
        if limit and len(urls) >= limit:
            break
    return urls[:limit] if limit else urls


def handle(u, html):
    m = re.search(r'itemprop="price"\s+content="([0-9.]+)"', html)
    if not m:
        return []
    p = sane_price(float(m.group(1)))
    if not p:
        return []
    img = re.search(r'property="og:image"\s+content="([^"]+)"', html)
    t = re.search(r"<title[^>]*>([^<]+)</title>", html)
    name = (t.group(1).rsplit(" | ", 1)[0].strip() if t else u.rsplit("/", 1)[-1])
    ean = re.search(r'"gtin\d*"\s*:\s*"?(\d{8,14})"?', html)
    skm = re.search(r"-(\d{7,9})$", u)
    # Magento renders a placeholder price ("1,00 kr.") on out-of-stock
    # product pages - verified live 2026-10-18 (3/3 OOS pages carried
    # data-price-amount="1" + schema.org/OutOfStock while the real price
    # is unset). Record the stock state and drop the placeholder row; a
    # genuine 1.00 product that is ALSO out of stock is vanishingly rare.
    oos = "schema.org/OutOfStock" in html
    in_stock = False if oos else (True if "schema.org/InStock" in html else None)
    if oos and p == 1.0:
        return []
    return [{
        "chain": "bauhaus_cz",
        "country": "cz",
        "currency": "CZK",
        "sku": skm.group(1) if skm else None,
        "ean": ean.group(1) if ean else None,
        "name": name,
        "url": u,
        "price": p,
        "in_stock": in_stock,
        "image": img.group(1).strip() if img else None,
    }]


def scrape(limit=None, deadline=None):
    return scrape_with_checkpoint("bauhaus_cz", fetch_url_list(limit), handle, limit, deadline)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = scrape(lim)
    write_jsonl(OUT, rows)
    print("bauhaus_cz: %d products -> %s" % (len(rows), OUT))
