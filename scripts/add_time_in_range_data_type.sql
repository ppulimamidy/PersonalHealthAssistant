-- Add TIME_IN_RANGE data type to the datatype enum
-- This is a common CGM metric that represents the percentage of time glucose levels are within target range

-- Add new enum value to the datatype enum
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'TIME_IN_RANGE';

-- Verify the new value was added
SELECT 'TIME_IN_RANGE'::datatype AS data_type; 