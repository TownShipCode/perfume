-- Add thumbnail_url for multi-channel commerce (WhatsApp, Facebook Shops, Instagram)
ALTER TABLE products ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
