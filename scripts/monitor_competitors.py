"""
Competitor Price Monitor — Scrape FFC and Fragrance Boutique pricing.

Usage:
    python scripts/monitor_competitors.py              # Run once, print comparison
    python scripts/monitor_competitors.py --json       # Output as JSON
    python scripts/monitor_competitors.py --watch 24   # Run every 24 hours

Saves results to data/competitor_prices.json for historical tracking.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "competitor_prices.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-ZA,en;q=0.9",
}


@dataclass
class CompetitorProduct:
    name: str
    price: float
    size_ml: int | None = None
    category: str = ""
    url: str = ""

@dataclass
class CompetitorSnapshot:
    source: str
    url: str
    scraped_at: str = ""
    products: list[CompetitorProduct] = field(default_factory=list)
    error: str = ""


# ── FFC Scraper ──

def scrape_ffc() -> CompetitorSnapshot:
    """Scrape Fine Fragrance Collection agent pricing."""
    snapshot = CompetitorSnapshot(
        source="Fine Fragrance Collection",
        url="https://finefragrancecollection.com/en-ZA/",
        scraped_at=datetime.now(timezone.utc).isoformat(),
    )
    try:
        resp = requests.get(snapshot.url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # FFC has product cards with data attributes or structured markup
        # We look for product containers
        products: list[CompetitorProduct] = []
        for card in soup.select("[data-product], .product, .product-item, .shop-item"):
            name_el = card.select_one(".product-name, .product-title, h3, h4")
            price_el = card.select_one(".product-price, .price, .amount")
            if name_el and price_el:
                name = name_el.get_text(strip=True)
                try:
                    price_text = price_el.get_text(strip=True).replace("R", "").replace(",", "").strip()
                    price = float(price_text)
                except (ValueError, TypeError):
                    continue
                products.append(CompetitorProduct(name=name, price=price, size_ml=30))

        snapshot.products = products
    except requests.RequestException as e:
        snapshot.error = str(e)
    return snapshot


# ── Fragrance Boutique Scraper ──

def scrape_fragrance_boutique() -> CompetitorSnapshot:
    """Scrape Fragrance Boutique pricing from WooCommerce."""
    snapshot = CompetitorSnapshot(
        source="Fragrance Boutique",
        url="https://fragranceboutique.co.za/shop/",
        scraped_at=datetime.now(timezone.utc).isoformat(),
    )
    try:
        resp = requests.get(snapshot.url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        products: list[CompetitorProduct] = []
        for card in soup.select(".product, .product-item, li.product"):
            name_el = card.select_one(".woocommerce-loop-product__title, .product-name, h2, h3")
            price_el = card.select_one(".price, .woocommerce-Price-amount, .amount")
            if name_el and price_el:
                name = name_el.get_text(strip=True)
                try:
                    price_text = price_el.get_text(strip=True).replace("R", "").replace(",", "").strip()
                    price = float(price_text)
                except (ValueError, TypeError):
                    continue
                products.append(CompetitorProduct(name=name, price=price))

        snapshot.products = products
    except requests.RequestException as e:
        snapshot.error = str(e)
    return snapshot


# ── Perfumes for Africa Scraper ──

def scrape_perfumes_for_africa() -> CompetitorSnapshot:
    """Scrape Perfumes for Africa homepage pricing."""
    snapshot = CompetitorSnapshot(
        source="Perfumes for Africa",
        url="https://perfumesforafrica.co.za/",
        scraped_at=datetime.now(timezone.utc).isoformat(),
    )
    try:
        resp = requests.get(snapshot.url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # They have price tables on the homepage
        products: list[CompetitorProduct] = []
        # Look for price table rows
        for row in soup.select("table tr"):
            cells = row.select("td")
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                try:
                    price_text = cells[-1].get_text(strip=True).replace("R", "").replace(",", "")
                    price = float(price_text) if price_text else 0
                except (ValueError, TypeError):
                    continue
                if name and price > 0:
                    products.append(CompetitorProduct(name=name, price=price))

        snapshot.products = products
    except requests.RequestException as e:
        snapshot.error = str(e)
    return snapshot


# ── Comparison & Reporting ──

def load_historical() -> dict[str, Any]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"snapshots": []}

def save_snapshot(snapshots: list[CompetitorSnapshot]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_historical()
    data["snapshots"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "source": s.source,
                "url": s.url,
                "product_count": len(s.products),
                "avg_price": round(sum(p.price for p in s.products) / len(s.products), 2) if s.products else 0,
                "min_price": min((p.price for p in s.products), default=0),
                "max_price": max((p.price for p in s.products), default=0),
                "error": s.error,
                "products": [{"name": p.name, "price": p.price} for p in s.products[:20]],  # Top 20 only
            }
            for s in snapshots
        ],
    })
    DATA_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

def print_comparison(snapshots: list[CompetitorSnapshot]) -> None:
    print(f"\n{'='*60}")
    print(f"  Competitor Price Report — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*60}\n")
    for s in snapshots:
        print(f"  {s.source} ({s.url})")
        if s.error:
            print(f"    ❌ Error: {s.error}\n")
            continue
        print(f"    Products found: {len(s.products)}")
        if s.products:
            prices = [p.price for p in s.products]
            print(f"    Price range: R{min(prices):.2f} – R{max(prices):.2f}")
            print(f"    Average price: R{sum(prices)/len(prices):.2f}")
            print(f"    Sample:")
            for p in sorted(s.products, key=lambda x: x.price)[:5]:
                print(f"      • {p.name}: R{p.price:.2f}")
        print()

def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor competitor pricing")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--watch", type=int, metavar="HOURS", help="Run every N hours")
    args = parser.parse_args()

    scrapers = [scrape_ffc, scrape_fragrance_boutique, scrape_perfumes_for_africa]

    while True:
        snapshots = []
        for scraper in scrapers:
            try:
                snapshots.append(scraper())
            except Exception as e:
                snapshots.append(CompetitorSnapshot(
                    source=scraper.__name__,
                    url="",
                    error=str(e),
                ))

        save_snapshot(snapshots)

        if args.json:
            print(json.dumps([
                {"source": s.source, "count": len(s.products), "error": s.error,
                 "products": [{"name": p.name, "price": p.price} for p in s.products]}
                for s in snapshots
            ], indent=2))
        else:
            print_comparison(snapshots)

        if not args.watch:
            break
        print(f"  Next run in {args.watch}h...")
        time.sleep(args.watch * 3600)


if __name__ == "__main__":
    main()
