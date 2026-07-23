# Product Images

Drop product images here. Then upload to Vercel Blob:

```powershell
Push-Location dashboard
vercel blob add product-images/focus-logic-1L.png
Pop-Location
```

Copy the CDN URL from the output and paste it into the dashboard product form.

## Current products

| Product | File | CDN URL |
|---------|------|---------|
| Focus Logic Herbal Blend 1L | `focus-logic-1L.png` | TBD |

## Image guidelines

- Square or portrait orientation
- Clear product on plain background
- No price text on the image (price lives in the database)
- Max 1MB for fast WhatsApp delivery
