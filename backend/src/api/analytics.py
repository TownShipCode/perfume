"""Analytics API — order metrics, revenue, top products, daily trends."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from src.db.connection import Database, fetch_all, fetch_one
from src.middleware.auth import require_dashboard_api_key

router = APIRouter(prefix="/api/analytics", tags=["analytics"], dependencies=[Depends(require_dashboard_api_key)])


@router.get("/summary")
async def get_summary(request: Request) -> dict:
    database: Database = request.app.state.database

    total_orders = await fetch_one(database, "SELECT COUNT(*) as count FROM orders")
    pending_pop = await fetch_one(database, "SELECT COUNT(*) as count FROM orders WHERE status = 'pop_received'")
    confirmed = await fetch_one(database, "SELECT COUNT(*) as count FROM orders WHERE status = 'confirmed'")
    revenue = await fetch_one(database, "SELECT COALESCE(SUM(total), 0) as total FROM orders WHERE status = 'confirmed'")
    active_products = await fetch_one(database, "SELECT COUNT(*) as count FROM products WHERE is_active = TRUE")

    try:
        top_products_rows = await fetch_all(
            database,
            """SELECT p.id, p.name, COUNT(oi.id) as order_count, SUM(oi.quantity) as total_qty
               FROM order_items oi JOIN products p ON p.id = oi.product_id
               GROUP BY p.id, p.name ORDER BY total_qty DESC LIMIT 5""",
        )
    except Exception:
        top_products_rows = []

    try:
        status_breakdown = await fetch_all(
            database, "SELECT status, COUNT(*) as count FROM orders GROUP BY status ORDER BY count DESC",
        )
    except Exception:
        status_breakdown = []

    return {
        "total_orders": total_orders["count"] if total_orders else 0,
        "pending_pop": pending_pop["count"] if pending_pop else 0,
        "confirmed": confirmed["count"] if confirmed else 0,
        "revenue": float(revenue["total"]) if revenue else 0,
        "active_products": active_products["count"] if active_products else 0,
        "top_products": [dict(p) for p in top_products_rows],
        "status_breakdown": [dict(s) for s in status_breakdown],
    }


@router.get("/daily")
async def get_daily(request: Request) -> dict:
    database: Database = request.app.state.database

    if database.mode == "postgres":
        query = """SELECT DATE(created_at) as day, COUNT(*) as orders, COALESCE(SUM(total), 0) as revenue
                   FROM orders WHERE created_at >= NOW() - INTERVAL '7 days'
                   GROUP BY DATE(created_at) ORDER BY day ASC"""
    else:
        query = """SELECT DATE(created_at) as day, COUNT(*) as orders, COALESCE(SUM(total), 0) as revenue
                   FROM orders WHERE created_at >= DATE('now', '-7 days')
                   GROUP BY DATE(created_at) ORDER BY day ASC"""

    rows = await fetch_all(database, query)
    return {"daily": [{"day": str(r["day"]), "orders": r["orders"], "revenue": float(r["revenue"])} for r in rows]}
