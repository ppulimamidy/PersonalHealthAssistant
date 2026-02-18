#!/bin/bash

# ============================================================================
# Demo Data Loader for Personal Health Assistant
# ============================================================================
# This script helps you load the research-backed synthetic demo data
# for Sarah Chen, a 52-year-old female with prediabetes, hypertension,
# hypothyroidism, and mild anxiety.
# ============================================================================

set -e  # Exit on error

echo "========================================="
echo "Personal Health Assistant - Demo Data Loader"
echo "========================================="
echo ""

# Check if user_id is provided
if [ -z "$1" ]; then
    echo "ERROR: User ID not provided"
    echo ""
    echo "Usage: ./load_demo_data.sh <user_id>"
    echo ""
    echo "Steps:"
    echo "1. Create demo user in Supabase Auth:"
    echo "   Email: sarah.chen.demo@example.com"
    echo "   Password: Demo123!@#"
    echo ""
    echo "2. Get the user_id from auth.users table"
    echo ""
    echo "3. Run this script:"
    echo "   ./load_demo_data.sh YOUR-USER-ID-HERE"
    echo ""
    exit 1
fi

USER_ID=$1

echo "Demo User ID: $USER_ID"
echo ""

# Create output directory
OUTPUT_DIR="/Users/pulimap/PersonalHealthAssistant/sarah"
mkdir -p "$OUTPUT_DIR"
echo "Creating output directory: $OUTPUT_DIR"
echo ""

# Copy and process SQL files
echo "Processing SQL files..."

for file in demo_data_seed.sql demo_data_seed_part2.sql demo_data_seed_symptoms.sql; do
    if [ ! -f "$file" ]; then
        echo "ERROR: File not found: $file"
        exit 1
    fi

    echo "  - Processing $file..."
    sed "s/demo_user_sarah_chen/$USER_ID/g" "$file" > "$OUTPUT_DIR/$file"
done

echo ""
echo "✅ Files processed successfully!"
echo ""
echo "========================================="
echo "NEXT STEPS - Load Data in Supabase"
echo "========================================="
echo ""
echo "📁 Processed files are in: $OUTPUT_DIR"
echo ""
echo "1. Open Supabase SQL Editor: https://supabase.com/dashboard/project/YOUR-PROJECT/sql"
echo ""
echo "2. Run these files IN ORDER:"
echo ""
echo "   📄 File 1: $OUTPUT_DIR/demo_data_seed.sql"
echo "      (User profile, conditions, medications, adherence logs)"
echo ""
echo "   📄 File 2: $OUTPUT_DIR/demo_data_seed_part2.sql"
echo "      (Nutrition meals - 30 days)"
echo ""
echo "   📄 File 3: $OUTPUT_DIR/demo_data_seed_symptoms.sql"
echo "      (Symptom journal - 30 days)"
echo ""
echo "3. Verify data loaded:"
echo ""
echo "   SELECT COUNT(*) FROM health_conditions WHERE user_id = '$USER_ID';  -- Should be 4"
echo "   SELECT COUNT(*) FROM medications WHERE user_id = '$USER_ID';  -- Should be 3"
echo "   SELECT COUNT(*) FROM supplements WHERE user_id = '$USER_ID';  -- Should be 3"
echo "   SELECT COUNT(*) FROM medication_adherence_logs WHERE user_id = '$USER_ID';  -- Should be ~180"
echo "   SELECT COUNT(*) FROM nutrition_meals WHERE user_id = '$USER_ID';  -- Should be ~90"
echo "   SELECT COUNT(*) FROM symptom_journal WHERE user_id = '$USER_ID';  -- Should be ~30"
echo ""
echo "4. Login and explore:"
echo "   📧 Email: sarah.chen.demo@example.com"
echo "   🔑 Password: Demo123!@#"
echo ""
echo "========================================="
echo ""
