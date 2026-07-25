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
        name="Focus Logic Herbal Blend 500ml",
        price="180.00",
        image_url="https://biomed-production.up.railway.app/static/focus-logic-500ml.png",
        description="Half-size 500ml bottle. Same blend. 1/4 cup daily.",
        keywords=[
            "500ml", "500 ml", "half", "small",
            "focus logic 500ml", "fl 500ml",
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
    "name": "Focus Logic 500ml",
    "price": "180.00",
    "image_url": "https://biomed-production.up.railway.app/static/focus-logic-500ml.png",
    "description": "Half-size bottle",
    "keywords": ["500ml", "half", "small"]
  }'
```

## Image hosting

Images must be publicly accessible URLs (WhatsApp fetches them). Current approach:

- **Production**: Serve from Railway at `https://biomed-production.up.railway.app/static/<filename>`
- **Add image**: Drop file in `backend/static/`, it auto-deploys with Railway
- **Alternative**: Vercel Blob (`npx vercel blob put` from `dashboard/`)
- The catalogue flow now attaches the first available product image to the WhatsApp catalogue reply as a captioned image, so seeding `image_url` is enough for the live flow to show it.

## Keyword tips

- Keywords are what users type to match products (e.g., "1 FL 1L" matches keyword "fl 1l")
- Include common misspellings and shorthand
- Longer keywords are matched first (e.g., "focus logic 1l" before "focus")
- Add the product number as a keyword if users might order by number

## Current products

| # | Name | Price | Image |
|---|------|-------|-------|
| 1 | Focus Logic Herbal Blend 1L | R330.00 | `/static/focus-logic-1L.png` |
