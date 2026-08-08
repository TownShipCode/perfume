# Adding Products

**Last updated: 2026-07-25**

## Ways to add a product

### Option A: Seed script (local dev)

1. Add a product image to `images/`
2. Copy it to `backend/static/`
3. Edit `backend/scripts/seed_focus_logic.py` and add a `create_product()` call
4. Run from `backend/`:
   ```powershell
   python -m scripts.seed_focus_logic
   ```

Example product entry:
```python
await create_product(
    database,
    ProductInput(
        product_number=2,
        name="Rose Oud 100ml",
        price="85.00",
        image_url="https://zenfragrances.vercel.app/static/rose-oud.png",
        description="Warm rose & oud — our signature scent.",
        keywords=[
            "rose", "oud", "rose oud", "100ml",
        ],
    ),
)
```

### Option B: Dashboard (production)

1. Upload image to Vercel Blob or serve from Railway `/static/`
2. Go to `https://biomed-dashboard-five.vercel.app`
3. Products → Add Product
4. Fill in: product number, name, price, image URL, description, keywords

### Option C: API (automation)

```powershell
curl -X POST https://biomed-production.up.railway.app/api/products \
  -H "X-API-Key: $DASHBOARD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "product_number": 2,
    "name": "Rose Oud 100ml",
    "price": "85.00",
    "image_url": "https://zenfragrances.vercel.app/static/rose-oud.png",
    "description": "Warm rose & oud — our signature scent.",
    "keywords": ["rose", "oud", "rose oud"]
  }'
```

## Image hosting

Images must be publicly accessible URLs (WhatsApp fetches them). Current approach:

- **Production**: Serve from Railway at `https://biomed-production.up.railway.app/static/<filename>`
- **Add image**: Drop file in `backend/static/`, it auto-deploys with Railway
- **Alternative**: Vercel Blob (`npx vercel blob put` from `dashboard/`)
- The catalogue flow now attaches the first available product image to the WhatsApp catalogue reply as a captioned image, so seeding `image_url` is enough for the live flow to show it.

## Keyword tips

- Keywords are what users type to match products (e.g., "rose oud 1l" matches keyword "rose oud")
- Include common misspellings and shorthand
- Longer keywords are matched first (e.g., "rose oud 1l" before "rose")
- Add the product number as a keyword if users might order by number

## Current products

| # | Name | Price | Image |
|---|------|-------|-------|
| 1 | Rose Oud 100ml | R85.00 | `/static/rose-oud.png` |
