-- 017_fix_customers_email_unique.sql
--
-- PROBLEM
-- Migration 009 makes customers.email `NOT NULL DEFAULT ''`, so WhatsApp
-- auto-created customers (get_or_create_customer) all get email = ''.
-- Migration 014 then created a FULL unique index on LOWER(email), which means
-- only ONE customer row may have email='' (the empty default). The second new
-- phone number that messages the bot fails to insert with:
--   UniqueViolationError: duplicate key ... "idx_customers_email_unique"
--   Key (lower(email))=() already exists.
-- and the bot replies "Something went wrong." (action=internal_error).
--
-- FIX
-- Replace the full unique index with a PARTIAL unique index so uniqueness is
-- only enforced for real, non-empty emails. Empty-email WhatsApp customers can
-- then be created freely, while duplicate email registrations are still blocked.

DROP INDEX IF EXISTS idx_customers_email_unique;

CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email_unique
    ON customers (LOWER(email))
    WHERE email <> '';
