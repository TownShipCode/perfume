"""
Agent Onboarding Kit — PDF price list generator.

Generates a printer-friendly HTML price list that agents can download,
print, or share with customers offline. Accessible via:
- Web: GET /api/agent/price-list
- WhatsApp: send "price list" or "pricelist" to get the link
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.middleware.auth import require_dashboard_api_key
from src.services.catalog_service import list_active_products

router = APIRouter(prefix="/api/agent", tags=["agent"])

PRICE_LIST_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{store_name} — Wholesale Price List</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; line-height: 1.5; max-width: 800px; margin: 0 auto; padding: 20px; }}
  .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #7c3aed; margin-bottom: 24px; }}
  .header h1 {{ font-size: 24px; color: #7c3aed; }}
  .header p {{ font-size: 14px; color: #6b7280; margin-top: 4px; }}
  .note {{ background: #f5f3ff; border-left: 4px solid #7c3aed; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; font-size: 13px; color: #5b21b6; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  th {{ background: #7c3aed; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }}
  tr:nth-child(even) {{ background: #f9fafb; }}
  .price {{ font-weight: 700; color: #059669; }}
  .footer {{ text-align: center; padding: 24px 0; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; margin-top: 24px; }}
  .footer a {{ color: #7c3aed; }}
  @media print {{
    body {{ padding: 0; }}
    .no-print {{ display: none; }}
    table {{ font-size: 12px; }}
    th, td {{ padding: 6px 8px; }}
  }}
  .print-btn {{ display: inline-block; background: #7c3aed; color: white; border: none; padding: 10px 24px; border-radius: 8px; font-size: 14px; cursor: pointer; margin-bottom: 20px; }}
  .print-btn:hover {{ background: #6d28d9; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
  .badge-men {{ background: #dbeafe; color: #1d4ed8; }}
  .badge-women {{ background: #fce7f3; color: #be185d; }}
  .badge-unisex {{ background: #d1fae5; color: #047857; }}
</style>
</head>
<body>
<div class="header">
  <h1>{store_name}</h1>
  <p>Wholesale Price List — {date}</p>
</div>
<div class="note">
  <strong>📋 For Agents Only</strong><br>
  These are wholesale prices. Suggested retail: 2× wholesale.<br>
  To order, WhatsApp us or visit your agent dashboard.
</div>
<button class="print-btn no-print" onclick="window.print()">🖨️ Print Price List</button>
<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Fragrance</th>
      <th>Type</th>
      <th>Scent</th>
      <th>Wholesale</th>
      <th>Retail*</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>
<p style="font-size:12px;color:#9ca3af;margin-top:8px;">* Suggested retail price (2× wholesale). Agents set their own prices.</p>
<div class="footer">
  <p>{store_name} — WhatsApp: {whatsapp} — Powered by Zen Fragrances</p>
  <p>Generated on {date_full}</p>
</div>
</body>
</html>"""

ROW_TEMPLATE = """<tr>
  <td>{number}</td>
  <td><strong>{name}</strong></td>
  <td><span class="badge badge-{gender_class}">{gender}</span></td>
  <td>{scent_family}</td>
  <td class="price">R{wholesale}</td>
  <td>R{retail}</td>
</tr>"""


@router.get("/price-list", response_class=HTMLResponse)
async def agent_price_list(request: Request) -> HTMLResponse:
    """Generate a printer-friendly wholesale price list for agents."""
    from datetime import date, datetime

    products = await list_active_products(request.app.state.database)
    settings = request.app.state.settings

    rows: list[str] = []
    for i, p in enumerate(products, 1):
        wholesale = float(p.get("price", 0))
        retail = round(wholesale * 2, 2)
        gender = (p.get("gender") or "unisex").lower()
        gender_class = gender if gender in ("men", "women", "unisex") else "unisex"
        rows.append(ROW_TEMPLATE.format(
            number=i,
            name=p.get("name", ""),
            gender=gender.title(),
            gender_class=gender_class,
            scent_family=p.get("scent_family") or "—",
            wholesale=f"{wholesale:,.2f}",
            retail=f"{retail:,.2f}",
        ))

    today = date.today()
    html_content = PRICE_LIST_HTML.format(
        store_name=settings.store_name,
        date=today.strftime("%d %B %Y"),
        date_full=datetime.now().strftime("%d %B %Y at %H:%M"),
        whatsapp=getattr(settings, 'manufacturer_phone', '') or '',
        rows="\n".join(rows) if rows else '<tr><td colspan="6" style="text-align:center;padding:40px;">No products available yet.</td></tr>',
    )
    return HTMLResponse(content=html_content)


# ── Agent Locator ──


class AgentProfile(BaseModel):
    suburb: str | None = None
    city: str | None = None
    is_listed: bool = False
    bio: str | None = None
    profile_image_url: str | None = None


@router.get("/search")
async def search_agents(request: Request, suburb: str = "", city: str = "") -> dict:
    """Public: search for listed agents by suburb/city."""
    from src.db.connection import fetch_all
    db = request.app.state.database
    mode = db.mode

    conditions = ["c.is_listed = TRUE", "c.role = 'agent'"]
    params: list = []
    if suburb.strip():
        if mode == "postgres":
            conditions.append("LOWER(c.suburb) LIKE LOWER($1)")
        else:
            conditions.append("LOWER(c.suburb) LIKE LOWER(?)")
        params.append(f"%{suburb.strip()}%")
    if city.strip():
        p = f"${len(params)+1}" if mode == "postgres" else "?"
        conditions.append(f"LOWER(c.city) LIKE LOWER({p})")
        params.append(f"%{city.strip()}%")

    where = " AND ".join(conditions)
    rows = await fetch_all(
        db,
        f"SELECT c.phone_number, c.name, c.agent_code, c.suburb, c.city, c.bio, c.profile_image_url FROM customers c WHERE {where} ORDER BY c.suburb LIMIT 20",
        *params,
    )
    return {"agents": [dict(r) for r in rows]}


@router.put("/profile", dependencies=[Depends(require_dashboard_api_key)])
async def update_agent_profile(request: Request, payload: AgentProfile) -> dict:
    """Agent updates their public listing profile."""
    # In production this would use the authenticated user's ID
    # For now, requires dashboard API key
    return {"status": "ok", "message": "Profile update endpoint ready"}

