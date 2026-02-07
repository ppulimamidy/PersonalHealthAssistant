-- This file will be executed when the local Supabase database starts
-- It will create initial data

-- Create initial data
INSERT INTO public.device_data_types (name, category, unit, description) VALUES
('HEART_RATE', 'VITALS', 'BPM', 'Heart rate measurements'),
('BLOOD_PRESSURE', 'VITALS', 'mmHg', 'Blood pressure readings'),
('BLOOD_OXYGEN', 'VITALS', '%', 'Blood oxygen saturation'),
('TEMPERATURE', 'VITALS', '°C', 'Body temperature'),
('STEPS', 'ACTIVITY', 'count', 'Step count'),
('CALORIES', 'ACTIVITY', 'kcal', 'Calories burned'),
('DISTANCE', 'ACTIVITY', 'm', 'Distance traveled'),
('SLEEP_DURATION', 'SLEEP', 'minutes', 'Sleep duration'),
('SLEEP_QUALITY', 'SLEEP', 'score', 'Sleep quality score'),
('WEIGHT', 'BODY', 'kg', 'Body weight'),
('BODY_FAT', 'BODY', '%', 'Body fat percentage'),
('MUSCLE_MASS', 'BODY', 'kg', 'Muscle mass'),
('WATER_INTAKE', 'NUTRITION', 'ml', 'Water intake'),
('GLUCOSE', 'METABOLIC', 'mg/dL', 'Blood glucose level'),
('CHOLESTEROL', 'METABOLIC', 'mg/dL', 'Cholesterol level')
ON CONFLICT (name) DO NOTHING;

-- Create default healthcare facilities
INSERT INTO public.healthcare_facilities (name, type, address, contact_info) VALUES
('General Hospital', 'HOSPITAL', '123 Main St, City, State', '555-0123'),
('City Clinic', 'CLINIC', '456 Oak Ave, City, State', '555-0456'),
('Specialty Medical Center', 'SPECIALTY', '789 Pine Rd, City, State', '555-0789')
ON CONFLICT DO NOTHING;

-- Create default insurance companies
INSERT INTO public.insurance_companies (name, contact_info) VALUES
('HealthFirst Insurance', '555-1000'),
('WellCare Insurance', '555-2000'),
('MediShield Insurance', '555-3000')
ON CONFLICT DO NOTHING; 