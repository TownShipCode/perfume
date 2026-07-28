ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS yoco_checkout_id TEXT UNIQUE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS yoco_event_id TEXT UNIQUE;

-- Index for email-based login (Phase 7 fix)
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- Unique constraint to prevent duplicate email registrations
CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email_unique ON customers(LOWER(email));
