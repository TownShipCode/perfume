-- 015_agent_locator.sql
-- Agent locator: suburb listing + public profile for Find an Agent feature

-- Add locator fields (city+suburb likely exist from address fields — skip if exists)
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we handle this in code
ALTER TABLE customers ADD COLUMN IF NOT EXISTS suburb TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_listed BOOLEAN DEFAULT FALSE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS profile_image_url TEXT;

-- Index for suburb search (only on listed agents)
CREATE INDEX IF NOT EXISTS idx_customers_suburb_listed ON customers(suburb) WHERE is_listed = TRUE;
