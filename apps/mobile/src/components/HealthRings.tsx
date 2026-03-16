/**
 * Health Rings — 4 concentric rings showing daily health progress.
 *
 * Outer:     Sleep (hours vs goal)
 * Mid-outer: Heart (HRV vs baseline)
 * Mid-inner: Activity (steps vs goal)
 * Inner:     Recovery (readiness score vs 100)
 *
 * Center shows overall health score (0–100).
 */

import { View, Text } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface RingData {
  sleep: { value: number; goal: number };       // hours
  heart: { value: number; goal: number };       // HRV ms
  activity: { value: number; goal: number };    // steps
  recovery: { value: number; goal: number };    // readiness 0-100
  overallScore: number | null;                  // 0-100
}

interface RingConfig {
  key: keyof Omit<RingData, 'overallScore'>;
  label: string;
  color: string;
  trackColor: string;
  unit: string;
  formatValue: (v: number) => string;
}

const RINGS: RingConfig[] = [
  {
    key: 'sleep',
    label: 'Sleep',
    color: '#818CF8',
    trackColor: '#818CF815',
    unit: 'h',
    formatValue: (v) => v.toFixed(1),
  },
  {
    key: 'heart',
    label: 'Heart',
    color: '#F87171',
    trackColor: '#F8717115',
    unit: 'ms',
    formatValue: (v) => Math.round(v).toString(),
  },
  {
    key: 'activity',
    label: 'Activity',
    color: '#6EE7B7',
    trackColor: '#6EE7B715',
    unit: '',
    formatValue: (v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : Math.round(v).toString(),
  },
  {
    key: 'recovery',
    label: 'Recovery',
    color: '#F59E0B',
    trackColor: '#F59E0B15',
    unit: '',
    formatValue: (v) => Math.round(v).toString(),
  },
];

// ─── Ring drawing helpers ─────────────────────────────────────────────────────

function clamp01(v: number): number {
  return Math.max(0, Math.min(1, v));
}

// ─── Component ────────────────────────────────────────────────────────────────

export function HealthRings({
  data,
  size = 200,
}: Readonly<{
  data: RingData;
  size?: number;
}>) {
  const cx = size / 2;
  const cy = size / 2;
  const strokeWidth = 10;
  const gap = 4;

  return (
    <View className="items-center">
      <View style={{ width: size, height: size }}>
        <Svg width={size} height={size}>
          {RINGS.map((ring, i) => {
            const radius = cx - strokeWidth / 2 - i * (strokeWidth + gap);
            if (radius <= 0) return null;
            const circumference = 2 * Math.PI * radius;
            const ringData = data[ring.key];
            const progress = clamp01(ringData.value / (ringData.goal || 1));
            const dashOffset = circumference * (1 - progress);

            return (
              <View key={ring.key}>
                {/* Track */}
                <Circle
                  cx={cx}
                  cy={cy}
                  r={radius}
                  stroke={ring.trackColor}
                  strokeWidth={strokeWidth}
                  fill="none"
                />
                {/* Progress arc */}
                <Circle
                  cx={cx}
                  cy={cy}
                  r={radius}
                  stroke={ring.color}
                  strokeWidth={strokeWidth}
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${circumference}`}
                  strokeDashoffset={dashOffset}
                  rotation={-90}
                  origin={`${cx}, ${cy}`}
                />
              </View>
            );
          })}
        </Svg>

        {/* Center score */}
        <View
          className="absolute items-center justify-center"
          style={{ top: 0, left: 0, width: size, height: size }}
        >
          <Text className="text-3xl font-display text-[#E8EDF5]">
            {data.overallScore != null ? Math.round(data.overallScore) : '—'}
          </Text>
          <Text className="text-[10px] text-[#526380] -mt-1">Health Score</Text>
        </View>
      </View>

      {/* Legend */}
      <View className="flex-row flex-wrap justify-center gap-x-4 gap-y-1 mt-3">
        {RINGS.map((ring) => {
          const rd = data[ring.key];
          const pct = Math.round(clamp01(rd.value / (rd.goal || 1)) * 100);
          return (
            <View key={ring.key} className="flex-row items-center gap-1">
              <View className="w-2 h-2 rounded-full" style={{ backgroundColor: ring.color }} />
              <Text className="text-[10px] text-[#526380]">
                {ring.label} {ring.formatValue(rd.value)}{ring.unit} ({pct}%)
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}
