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

import { useState } from 'react';
import { View, Text, TouchableOpacity, Modal, Pressable } from 'react-native';
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
  helpTip: string;
}

const RINGS: RingConfig[] = [
  {
    key: 'sleep',
    label: 'Sleep',
    color: '#818CF8',
    trackColor: '#818CF815',
    unit: 'h',
    formatValue: (v) => v.toFixed(1),
    helpTip: 'Total sleep duration last night. Goal is 7-9 hours for most adults. Good sleep improves recovery, focus, and immune function.',
  },
  {
    key: 'heart',
    label: 'Heart',
    color: '#F87171',
    trackColor: '#F8717115',
    unit: 'ms',
    formatValue: (v) => Math.round(v).toString(),
    helpTip: 'Heart Rate Variability (HRV) in milliseconds. Higher is generally better — it indicates your nervous system is adaptable and resilient to stress.',
  },
  {
    key: 'activity',
    label: 'Activity',
    color: '#6EE7B7',
    trackColor: '#6EE7B715',
    unit: '',
    formatValue: (v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : Math.round(v).toString(),
    helpTip: 'Daily step count from your phone or wearable. 8,000+ steps/day is associated with lower risk of heart disease and improved mood.',
  },
  {
    key: 'recovery',
    label: 'Recovery',
    color: '#F59E0B',
    trackColor: '#F59E0B15',
    unit: '',
    formatValue: (v) => Math.round(v).toString(),
    helpTip: 'How ready your body is to perform today (0-100). Based on sleep quality, HRV, and resting heart rate. Higher means you\'re well-recovered.',
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
  const [helpTip, setHelpTip] = useState<{ label: string; text: string; color: string } | null>(null);
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

        {/* Center score — tap for explanation */}
        <TouchableOpacity
          className="absolute items-center justify-center"
          style={{ top: 0, left: 0, width: size, height: size }}
          activeOpacity={0.7}
          onPress={() => setHelpTip({
            label: 'Health Score',
            text: 'Your daily score (0–100) is a weighted average of four pillars:\n\n• Sleep (35%) — hours slept vs 8-hour goal\n• Heart (30%) — HRV vs your 30-day baseline\n• Activity (25%) — steps vs 8,000 target\n• Recovery (10%) — readiness from your wearable or estimated\n\nHigher is better. Updates each time you sync.',
            color: '#00D4AA',
          })}
        >
          <Text className="text-3xl font-display text-[#E8EDF5]">
            {data.overallScore != null ? Math.round(data.overallScore) : '—'}
          </Text>
          <Text className="text-[10px] text-[#526380] -mt-1">Health Score</Text>
        </TouchableOpacity>
      </View>

      {/* Legend — tap for help */}
      <View className="flex-row flex-wrap justify-center gap-x-4 gap-y-1 mt-3">
        {RINGS.map((ring) => {
          const rd = data[ring.key];
          const pct = Math.round(clamp01(rd.value / (rd.goal || 1)) * 100);
          return (
            <TouchableOpacity
              key={ring.key}
              className="flex-row items-center gap-1"
              onPress={() => setHelpTip({ label: ring.label, text: ring.helpTip, color: ring.color })}
              activeOpacity={0.7}
            >
              <View className="w-2 h-2 rounded-full" style={{ backgroundColor: ring.color }} />
              <Text className="text-[10px] text-[#526380]">
                {ring.label} {ring.formatValue(rd.value)}{ring.unit} ({pct}%)
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Help tip modal */}
      <Modal visible={!!helpTip} transparent animationType="fade" onRequestClose={() => setHelpTip(null)}>
        <Pressable className="flex-1 items-center justify-center bg-black/60" onPress={() => setHelpTip(null)}>
          <View className="bg-[#0F1720] border border-surface-border rounded-2xl mx-8 p-5 max-w-sm">
            <View className="flex-row items-center gap-2 mb-2">
              <View className="w-3 h-3 rounded-full" style={{ backgroundColor: helpTip?.color }} />
              <Text className="text-[#E8EDF5] font-sansMedium text-base">{helpTip?.label}</Text>
            </View>
            <Text className="text-[#8B97A8] text-sm leading-5">{helpTip?.text}</Text>
            <TouchableOpacity onPress={() => setHelpTip(null)} className="mt-4 self-end">
              <Text className="text-primary-500 font-sansMedium text-sm">Got it</Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}
