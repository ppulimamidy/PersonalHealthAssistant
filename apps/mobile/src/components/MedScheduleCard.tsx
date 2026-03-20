/**
 * Medication Schedule Card — optimized daily timing for meds + supplements.
 */

import { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface ScheduleItem {
  name: string;
  type: 'medication' | 'supplement';
  rule: string;
  reason: string;
}

interface TimeSlot {
  time_slot: string;
  label: string;
  items: ScheduleItem[];
}

interface Props {
  schedule: TimeSlot[];
  supplementInteractions: Array<{ supp_a: string; supp_b: string; rule: string; reason: string }>;
}

const SLOT_ICONS: Record<string, string> = {
  morning_empty: 'sunny-outline',
  before_breakfast: 'sunny-outline',
  with_breakfast: 'cafe-outline',
  with_meals: 'restaurant-outline',
  with_fatty_meal: 'restaurant-outline',
  with_lunch: 'restaurant-outline',
  before_dinner: 'moon-outline',
  evening: 'moon-outline',
  bedtime: 'bed-outline',
  any_time: 'time-outline',
};

export default function MedScheduleCard({ schedule, supplementInteractions }: Readonly<Props>) {
  const [expanded, setExpanded] = useState(false);

  if (schedule.length === 0) return null;

  const totalItems = schedule.reduce((sum, slot) => sum + slot.items.length, 0);

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      <TouchableOpacity
        onPress={() => setExpanded((e) => !e)}
        className="flex-row items-center justify-between"
        activeOpacity={0.7}
      >
        <View className="flex-row items-center gap-2">
          <Ionicons name="time-outline" size={14} color="#818CF8" />
          <Text className="text-[#818CF8] text-xs uppercase tracking-wider font-sansMedium">
            Optimal Schedule
          </Text>
          <Text className="text-[#3D4F66] text-[10px]">{totalItems} items</Text>
        </View>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={14} color="#526380" />
      </TouchableOpacity>

      {/* Collapsed: just slot labels */}
      {!expanded && (
        <View className="flex-row flex-wrap gap-1.5 mt-2">
          {schedule.map((slot) => (
            <View key={slot.time_slot} className="bg-white/5 rounded-md px-2 py-0.5">
              <Text className="text-[#526380] text-[9px]">
                {slot.label}: {slot.items.length}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Expanded: full timeline */}
      {expanded && (
        <View className="mt-3">
          {schedule.map((slot, si) => {
            const icon = SLOT_ICONS[slot.time_slot] ?? 'time-outline';
            return (
              <View key={slot.time_slot} className="mb-3">
                {/* Slot header */}
                <View className="flex-row items-center gap-2 mb-1.5">
                  <Ionicons name={icon as never} size={12} color="#818CF8" />
                  <Text className="text-[#E8EDF5] text-xs font-sansMedium">{slot.label}</Text>
                </View>
                {/* Items */}
                {slot.items.map((item, ii) => (
                  <View key={ii} className="ml-5 mb-1.5 flex-row items-start gap-2">
                    <View
                      className="w-1.5 h-1.5 rounded-full mt-1.5"
                      style={{ backgroundColor: item.type === 'medication' ? '#00D4AA' : '#818CF8' }}
                    />
                    <View className="flex-1">
                      <Text className="text-[#8B9BB4] text-xs">{item.name}</Text>
                      <Text className="text-[#3D4F66] text-[10px]">{item.reason}</Text>
                    </View>
                  </View>
                ))}
                {/* Connector line */}
                {si < schedule.length - 1 && (
                  <View className="ml-1.5 h-2 w-px bg-[#1E2A3B]" />
                )}
              </View>
            );
          })}

          {/* Supplement interactions */}
          {supplementInteractions.length > 0 && (
            <View className="mt-2 pt-2 border-t border-surface-border">
              <Text className="text-[#F5A623] text-[10px] uppercase tracking-wider mb-1 font-sansMedium">
                Timing Notes
              </Text>
              {supplementInteractions.map((si, i) => (
                <View key={i} className="flex-row items-start gap-1.5 mb-1">
                  <Ionicons name="alert-circle-outline" size={10} color="#F5A623" />
                  <Text className="text-[#526380] text-[10px] flex-1">
                    {si.supp_a} + {si.supp_b}: {si.rule}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
    </View>
  );
}
