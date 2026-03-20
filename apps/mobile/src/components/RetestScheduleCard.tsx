/**
 * Retest Schedule Card — shows recommended upcoming lab tests
 * based on conditions and medications.
 */

import { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface RetestItem {
  test_type: string;
  last_date: string | null;
  interval_days: number;
  days_until_due: number;
  status: 'overdue' | 'due_soon' | 'on_track';
  reason: string;
}

interface Props {
  schedule: RetestItem[];
}

const STATUS_CONFIG = {
  overdue: { color: '#F87171', bg: '#F8717112', label: 'Overdue', icon: 'alert-circle' as const },
  due_soon: { color: '#F5A623', bg: '#F5A62312', label: 'Due soon', icon: 'time-outline' as const },
  on_track: { color: '#6EE7B7', bg: '#6EE7B712', label: 'On track', icon: 'checkmark-circle-outline' as const },
};

export default function RetestScheduleCard({ schedule }: Readonly<Props>) {
  const [expanded, setExpanded] = useState(false);

  if (schedule.length === 0) return null;

  const urgent = schedule.filter((s) => s.status === 'overdue' || s.status === 'due_soon');
  const hasUrgent = urgent.length > 0;

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      <TouchableOpacity
        onPress={() => setExpanded((e) => !e)}
        className="flex-row items-center justify-between"
        activeOpacity={0.7}
      >
        <View className="flex-row items-center gap-2">
          <Ionicons name="calendar-outline" size={14} color={hasUrgent ? '#F5A623' : '#526380'} />
          <Text className="text-[#526380] text-xs uppercase tracking-wider font-sansMedium">
            Recommended Labs
          </Text>
          {hasUrgent && (
            <View className="bg-[#F5A62320] rounded-full px-1.5 py-0.5">
              <Text className="text-[#F5A623] text-[9px] font-sansMedium">{urgent.length} due</Text>
            </View>
          )}
        </View>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={14} color="#526380" />
      </TouchableOpacity>

      {expanded && (
        <View className="mt-3 gap-2">
          {schedule.map((item, i) => {
            const cfg = STATUS_CONFIG[item.status];
            return (
              <View key={i} className="flex-row items-center gap-3 rounded-lg px-3 py-2" style={{ backgroundColor: cfg.bg }}>
                <Ionicons name={cfg.icon} size={14} color={cfg.color} />
                <View className="flex-1">
                  <Text className="text-[#E8EDF5] text-sm font-sansMedium">{item.test_type}</Text>
                  <Text className="text-[#526380] text-[10px] mt-0.5">
                    {item.reason}
                    {item.last_date ? ` · Last: ${item.last_date}` : ' · Never tested'}
                  </Text>
                </View>
                <Text className="text-xs font-sansMedium" style={{ color: cfg.color }}>
                  {item.status === 'overdue'
                    ? `${Math.abs(item.days_until_due)}d overdue`
                    : item.status === 'due_soon'
                    ? `${item.days_until_due}d`
                    : `${item.days_until_due}d`}
                </Text>
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
}
