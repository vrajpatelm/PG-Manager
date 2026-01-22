-- Add column for storing binary image data
ALTER TABLE owners
ADD COLUMN IF NOT EXISTS qr_code_data BYTEA;

-- Optional: Drop the old URL column if we want to fully switch, 
-- but keeping it for backward compatibility might be safer for a moment.
-- We will stop using it though.
