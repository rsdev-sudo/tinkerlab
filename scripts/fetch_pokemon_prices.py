#!/usr/bin/env python3
"""Refresh pokemon-higher-lower/cards.json from the free TCGdex API (no key needed).

Prices are TCGplayer market prices in USD, as returned by TCGdex.
Safe by design: if too few priced cards come back, it exits with an error and
does NOT overwrite the existing cards.json.
"""
import json, os, sys, time, datetime, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE = os.environ.get("TCGDEX_BASE", "https://api.tcgdex.net/v2/en")
OUT = os.environ.get("OUT_FILE", "pokemon-higher-lower/cards.json")
MIN_PRICE = 0.25     # ignore bulk cards worth less than this (USD)
MIN_CARDS = 100      # refuse to publish a suspiciously small list
WORKERS = 4

# Set names to include (matched case-insensitively against TCGdex set names).
WANTED_SETS = [
    "Base Set", "Jungle", "Fossil", "Team Rocket", "Neo Genesis", "Neo Destiny",
    "Ruby & Sapphire", "Diamond & Pearl", "HeartGold SoulSilver", "Black & White",
    "XY", "Evolutions", "Sun & Moon", "Hidden Fates", "Shining Fates",
    "Sword & Shield", "Vivid Voltage", "Brilliant Stars", "Evolving Skies",
    "Fusion Strike", "Crown Zenith", "Scarlet & Violet", "Obsidian Flames",
    "151", "Paldean Fates", "Temporal Forces", "Surging Sparks",
]

def get(path, tries=4):
    url = BASE + path
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "tinkerlab-price-refresh/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if i == tries - 1:
                print(f"  gave up on {path}: {e}", file=sys.stderr)
                return None
            time.sleep(1.5 * (i + 1))

def num(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None

def pick_price(card):
    tp = ((card.get("pricing") or {}).get("tcgplayer")) or {}
    variants = {k: v for k, v in tp.items() if isinstance(v, dict) and num(v.get("marketPrice")) is not None}
    if not variants:
        return None, None, None
    order = ["normal", "holofoil", "reverse-holofoil", "reverse", "1st-edition", "1st-edition-holofoil"]
    key = next((k for k in order if k in variants), next(iter(variants)))
    unit = tp.get("unit") or "USD"
    if unit != "USD":
        return None, None, None
    return round(num(variants[key]["marketPrice"]), 2), key, tp.get("updated")

def main():
    sets = get("/sets")
    if not sets:
        sys.exit("Could not fetch the set list")
    by_name = {s["name"].strip().lower(): s for s in sets if s.get("name")}
    chosen, missing = [], []
    for w in WANTED_SETS:
        s = by_name.get(w.lower())
        (chosen if s else missing).append(s or w)
    print(f"Matched {len(chosen)} sets; not found: {missing}")

    jobs = []
    for s in chosen:
        d = get(f"/sets/{s['id']}")
        if not d:
            continue
        cc = d.get("cardCount") or {}
        total = cc.get("official") or cc.get("total")
        for c in d.get("cards", []):
            jobs.append((d, total, c))
        time.sleep(0.2)
    print(f"{len(jobs)} cards to check")

    def work(job):
        d, total, c = job
        card = get(f"/cards/{c['id']}")
        time.sleep(0.1)
        if not card:
            return None
        price, variant, updated = pick_price(card)
        if price is None or price < MIN_PRICE:
            return None
        number = str(card.get("localId", c.get("localId", "")))
        return {
            "id": card.get("id", c["id"]),
            "name": card.get("name", c.get("name")),
            "set": (card.get("set") or {}).get("name") or d.get("name"),
            "year": (d.get("releaseDate") or "")[:4],
            "number": f"{number}/{total}" if total else number,
            "rarity": card.get("rarity"),
            "category": card.get("category"),
            "hp": card.get("hp"),
            "types": card.get("types"),
            "illustrator": card.get("illustrator"),
            "price": price,
            "variant": variant,
            "priceUpdated": updated,
        }

    with ThreadPoolExecutor(WORKERS) as ex:
        results = [r for r in ex.map(work, jobs) if r]

    print(f"{len(results)} priced cards kept")
    if len(results) < MIN_CARDS:
        sys.exit(f"Only {len(results)} priced cards (need {MIN_CARDS}); leaving cards.json unchanged")

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({
            "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
            "source": "TCGdex (TCGplayer market price, USD)",
            "cards": results,
        }, f, ensure_ascii=False, separators=(",", ":"))
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
