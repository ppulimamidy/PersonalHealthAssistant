#!/usr/bin/env bash
# Re-signs the Vitalix simulator build with the HealthKit entitlement and
# patches NSHealth usage descriptions into Info.plist, then reinstalls.
# Must run AFTER expo run:ios --no-bundler completes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTITLEMENTS="$SCRIPT_DIR/../ios/Vitalix/Vitalix.entitlements"
BUNDLE_ID="com.vitalix.app"

# Find build product
BUILD=$(find "$HOME/Library/Developer/Xcode/DerivedData" \
  -name "Vitalix.app" -path "*/Debug-iphonesimulator/*" 2>/dev/null | head -1)

if [ -z "$BUILD" ]; then
  echo "⚠️  No build product found — skipping re-sign"
  exit 0
fi

echo "📦 Build product: $BUILD"

# Patch Info.plist with HealthKit usage descriptions (idempotent)
/usr/libexec/PlistBuddy -c \
  "Add NSHealthShareUsageDescription string 'Vitalix reads your steps, sleep, heart rate, HRV, SpO2, and workout data to generate personalized health insights.'" \
  "$BUILD/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c \
  "Add NSHealthUpdateUsageDescription string 'Vitalix may write workout sessions you log in the app back to Apple Health.'" \
  "$BUILD/Info.plist" 2>/dev/null || true

# Sign the bundle (updates CodeResources to include patched Info.plist hash)
echo "🔏 Signing bundle..."
codesign --force --sign - --entitlements "$ENTITLEMENTS" "$BUILD"

# Reinstall into simulator
echo "📲 Reinstalling..."
xcrun simctl terminate booted "$BUNDLE_ID" 2>/dev/null || true
sleep 0.3
xcrun simctl uninstall booted "$BUNDLE_ID" 2>/dev/null || true
sleep 0.3
xcrun simctl install booted "$BUILD"

echo "✅ Done — tap Vitalix in the simulator to launch"
