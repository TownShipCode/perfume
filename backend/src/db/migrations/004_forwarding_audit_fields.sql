ALTER TABLE orders ADD COLUMN forward_message_id TEXT;
ALTER TABLE orders ADD COLUMN forward_error TEXT;
ALTER TABLE orders ADD COLUMN forward_payload TEXT;
ALTER TABLE orders ADD COLUMN forward_response TEXT;
ALTER TABLE orders ADD COLUMN forward_attempts INTEGER NOT NULL DEFAULT 0;
