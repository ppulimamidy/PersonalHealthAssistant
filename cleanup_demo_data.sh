#!/bin/bash

# ============================================================================
# Personal Health Assistant - Demo Data Cleanup Script
# ============================================================================
# Purpose: Delete all demo data to allow fresh reloading during testing
# Usage: ./cleanup_demo_data.sh <user_id>
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Personal Health Assistant - Demo Data Cleanup"
echo "========================================="
echo ""

# Check if user_id argument is provided
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: User ID not provided${NC}"
    echo ""
    echo "Usage: $0 <user_id>"
    echo ""
    echo "Example:"
    echo "  $0 22144dc2-f352-48aa-b34b-aebfa9f7e638"
    echo ""
    exit 1
fi

USER_ID="$1"

echo "Demo User ID: $USER_ID"
echo ""

# Create output directory for processed file
OUTPUT_DIR="./sarah"
mkdir -p "$OUTPUT_DIR"

# Process the cleanup SQL file
echo "Generating cleanup SQL file..."
sed "s/demo_user_sarah_chen/$USER_ID/g" cleanup_demo_data.sql > "$OUTPUT_DIR/cleanup_demo_data.sql"

echo -e "${GREEN}✅ Cleanup file generated!${NC}"
echo ""

# Display instructions
echo "========================================="
echo "NEXT STEPS - Run Cleanup in Supabase"
echo "========================================="
echo ""
echo "📁 Cleanup file: $OUTPUT_DIR/cleanup_demo_data.sql"
echo ""
echo "1. Open Supabase SQL Editor: https://supabase.com/dashboard/project/YOUR-PROJECT/sql"
echo ""
echo "2. Copy and paste the contents of:"
echo "   📄 $OUTPUT_DIR/cleanup_demo_data.sql"
echo ""
echo "3. Run the SQL script"
echo ""
echo "4. Verify all record counts show 0"
echo ""
echo -e "${YELLOW}⚠️  WARNING: This will DELETE ALL data for user: $USER_ID${NC}"
echo ""
echo "After cleanup, you can reload fresh demo data by running:"
echo "  ./load_demo_data.sh $USER_ID"
echo ""
echo "========================================="
