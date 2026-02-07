-- Add Dexcom CGM specific data types to the datatype enum
-- This migration adds the new data types that were added to the Python enum

-- Add new enum values to the datatype enum
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'GLUCOSE_CALIBRATION';
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'INSULIN_EVENT';
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'CARB_EVENT';
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'GLUCOSE_ALERT';
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'GLUCOSE_TREND';
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'SENSOR_STATUS';
ALTER TYPE datatype ADD VALUE IF NOT EXISTS 'TRANSMITTER_STATUS';

-- Verify the new values were added
SELECT unnest(enum_range(NULL::datatype)) AS data_type 
WHERE unnest(enum_range(NULL::datatype)) IN (
    'GLUCOSE_CALIBRATION',
    'INSULIN_EVENT',
    'CARB_EVENT',
    'GLUCOSE_ALERT',
    'GLUCOSE_TREND',
    'SENSOR_STATUS',
    'TRANSMITTER_STATUS'
); 