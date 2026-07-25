ALTER TABLE orders ADD COLUMN fl_pop_image_url TEXT;
ALTER TABLE orders ADD COLUMN fl_pop_uploaded_at TIMESTAMPTZ;
ALTER TABLE orders ADD COLUMN fl_amount DECIMAL(10,2);
