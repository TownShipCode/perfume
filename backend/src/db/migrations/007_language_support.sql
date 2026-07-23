ALTER TABLE customers ADD COLUMN language TEXT NOT NULL DEFAULT '';
ALTER TABLE message_templates ADD COLUMN language TEXT NOT NULL DEFAULT 'en';

-- Make (template_key, language) unique instead of just template_key
-- SQLite doesn't support DROP CONSTRAINT, so we handle this in connection.py
