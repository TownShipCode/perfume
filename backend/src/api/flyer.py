"""Consumer retail flyer — printable catalogue agents share on WhatsApp.

Generates a retail-facing HTML flyer (2× wholesale pricing) that agents can
forward, print, or share offline. Zero hardcoding: product names, prices,
images, edition and validity all come from the DB / today's date / settings.
- Web: GET /flyer (public, no auth)
- Edition stamp + validity window mirror the agent price list (see flyer-cadence.md)
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.services.catalog_service import list_active_products

router = APIRouter(tags=["flyer"])

FLYER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{store_name} — Retail Catalogue {edition}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; line-height: 1.5; max-width: 900px; margin: 0 auto; padding: 20px; }}
  .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #7c3aed; margin-bottom: 8px; }}
  .header h1 {{ font-size: 26px; color: #7c3aed; }}
  .header p {{ font-size: 14px; color: #6b7280; margin-top: 4px; }}
  .section-title {{ font-size: 18px; font-weight: 700; color: #7c3aed; margin: 28px 0 12px; }}
  .hero {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }}
  .group {{ margin-bottom: 24px; }}
  .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; text-align: center; }}
  .img-wrap {{ position: relative; height: 150px; background: #f5f3ff; overflow: hidden; }}
  .img-wrap img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
  .no-img {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 42px; font-weight: 800; color: #7c3aed; }}
  .card-body {{ padding: 10px 12px; }}
  .card-name {{ font-weight: 600; font-size: 14px; min-height: 40px; }}
  .card-price {{ color: #059669; font-weight: 800; font-size: 16px; }}
  .footer {{ text-align: center; padding: 24px 0; font-size: 13px; color: #6b7280; border-top: 1px solid #e5e7eb; margin-top: 24px; }}
  .cta {{ display: inline-block; background: #25d366; color: #fff; padding: 12px 28px; border-radius: 10px; font-weight: 700; font-size: 16px; margin: 12px 0; text-decoration: none; }}
  @media print {{
    body {{ padding: 0; }}
    .grid {{ grid-template-columns: repeat(4, 1fr); }}
    .card {{ break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="header">
  <h1>{store_name}</h1>
  <p>Retail Catalogue — <strong>Edition {edition}</strong></p>
  <p>Valid from {valid_from} · Valid until {valid_until}</p>
</div>

<div class="section-title">⭐ Featured Fragrances</div>
<div class="hero">
  {hero_cards}
</div>

<div class="section-title">📋 Full Catalogue</div>
{groups}

<div class="footer">
  <div><a class="cta" href="{whatsapp_link}" target="_blank" rel="noopener">📱 Order on WhatsApp</a></div>
  <p>Or send a product name — e.g. "5 Rose Oud" — to order directly on WhatsApp.</p>
  <p>{store_name} — Edition {edition} · Prices valid until {valid_until}</p>
</div>
</body>
</html>"""

CARD_TEMPLATE = """<div class="card">
  {media}
  <div class="card-body">
    <div class="card-name">{name}</div>
    <div class="card-price">R{retail}</div>
  </div>
</div>"""


def _card_media(name: str, image_url: str | None) -> str:
    """Product image with a graceful fallback to an initial-letter tile.

    The initial sits behind the image; if the image fails to load it is
    removed by JS and the initial shows through. No hardcoded images.
    """
    initial = name[0].upper() if name and name[0].strip() else "?"
    wrap = f'<div class="img-wrap"><div class="no-img">{initial}</div>'
    if image_url:
        safe = image_url.replace('"', "")
        wrap += f'<img src="{safe}" alt="{name}" loading="lazy" onerror="this.remove()">'
    return wrap + "</div>"


def _card(price: float, name: str, image_url: str | None) -> str:
    retail = round(price * 2, 2)
    return CARD_TEMPLATE.format(
        media=_card_media(name, image_url),
        name=name,
        retail=f"{retail:,.2f}",
    )


@router.get("/flyer", response_class=HTMLResponse)
async def consumer_flyer(request: Request) -> HTMLResponse:
    """Retail-facing printable flyer, generated from the DB (no hardcoding)."""
    from datetime import date, datetime  # noqa: F401
    import calendar
    import urllib.parse

    products = await list_active_products(request.app.state.database)
    settings = request.app.state.settings

    def image_for(p: dict) -> str | None:
        return p.get("thumbnail_url") or p.get("image_url")

    # Featured: explicit IDs from settings, else first 4 active products.
    featured = [p for p in products if p.get("product_number") in settings.flyer_featured_ids]
    if not featured:
        featured = products[:4]
    hero_cards = "".join(
        _card(float(p.get("price", 0)), p.get("name") or "—", image_for(p)) for p in featured
    )

    # Group the full catalogue by gender for consumer clarity.
    groups: list[str] = []
    for gender in ("men", "women", "unisex"):
        members = [p for p in products if (p.get("gender") or "unisex").lower() == gender]
        if not members:
            continue
        cards = "".join(
            _card(float(p.get("price", 0)), p.get("name") or "—", image_for(p)) for p in members
        )
        groups.append(
            f'<div class="group"><h3 class="section-title">{gender.title()}</h3>'
            f'<div class="grid">{cards}</div></div>'
        )
    groups_html = "\n".join(groups) if groups else "<p>No products available yet.</p>"

    today = date.today()
    first = today.replace(day=1)
    last = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    edition = today.strftime("%Y-%m")

    # WhatsApp CTA — from FLYER_WHATSAPP, falling back to ADMIN_PHONE. Not hardcoded.
    whatsapp = settings.flyer_whatsapp or settings.admin_phone or ""
    if whatsapp:
        digits = "".join(ch for ch in whatsapp if ch.isdigit())
        msg = urllib.parse.quote(f"Hi {settings.store_name}! I'd like to order a fragrance.")
        whatsapp_link = f"https://wa.me/{digits}?text={msg}"
    else:
        whatsapp_link = "#"

    html_content = FLYER_HTML.format(
        store_name=settings.store_name,
        edition=edition,
        valid_from=first.strftime("%d %B %Y"),
        valid_until=last.strftime("%d %B %Y"),
        hero_cards=hero_cards,
        groups=groups_html,
        whatsapp_link=whatsapp_link,
    )
    return HTMLResponse(content=html_content)
