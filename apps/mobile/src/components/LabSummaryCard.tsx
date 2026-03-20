/**
 * Lab Summary Card — groups biomarkers by body system with status indicators,
 * watch items, and doctor discussion points.
 */

import { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface BiomarkerEntry {
  name: string;
  value: number;
  unit: string;
  status: string;
  previous?: number;
  delta?: number;
  optimal_flag?: boolean;
  optimal_range?: string;
}

interface SystemGroup {
  key: string;
  name: string;
  icon: string;
  status: 'all_normal' | 'has_borderline' | 'has_abnormal';
  total: number;
  normal_count: number;
  biomarkers: BiomarkerEntry[];
}

interface WatchItem {
  biomarker: string;
  value: number;
  unit: string;
  status: string;
  delta_text: string;
}

interface DoctorItem {
  finding: string;
  what_it_means: string;
  what_to_ask: string;
  follow_up: string;
}

interface Props {
  systems: SystemGroup[];
  watchItems: WatchItem[];
  doctorDiscussion: DoctorItem[];
  homaIr?: number | null;
  testDate?: string;
}

const STATUS_COLORS = {
  all_normal: '#6EE7B7',
  has_borderline: '#F5A623',
  has_abnormal: '#F87171',
};

const BM_STATUS_COLORS: Record<string, string> = {
  normal: '#6EE7B7',
  borderline: '#F5A623',
  abnormal: '#F87171',
  critical: '#F87171',
  unknown: '#526380',
};

export default function LabSummaryCard({ systems, watchItems, doctorDiscussion, homaIr, testDate }: Readonly<Props>) {
  const [expandedSystem, setExpandedSystem] = useState<string | null>(null);
  const [showDoctor, setShowDoctor] = useState(false);

  if (systems.length === 0) return null;

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-2">
          <Ionicons name="document-text-outline" size={14} color="#00D4AA" />
          <Text className="text-[#526380] text-xs uppercase tracking-wider font-sansMedium">Lab Summary</Text>
        </View>
        {testDate && <Text className="text-[#3D4F66] text-[10px]">{testDate}</Text>}
      </View>

      {/* System rows */}
      {systems.map((sys) => {
        const isExpanded = expandedSystem === sys.key;
        const statusColor = STATUS_COLORS[sys.status];
        return (
          <View key={sys.key}>
            <TouchableOpacity
              onPress={() => setExpandedSystem(isExpanded ? null : sys.key)}
              className="flex-row items-center justify-between py-2"
              activeOpacity={0.7}
            >
              <View className="flex-row items-center gap-2">
                <View className="w-2 h-2 rounded-full" style={{ backgroundColor: statusColor }} />
                <Ionicons name={sys.icon as never} size={14} color="#526380" />
                <Text className="text-[#E8EDF5] text-sm">{sys.name}</Text>
              </View>
              <View className="flex-row items-center gap-2">
                <Text className="text-[#526380] text-[10px]">
                  {sys.normal_count}/{sys.total} normal
                </Text>
                <Ionicons name={isExpanded ? 'chevron-up' : 'chevron-down'} size={12} color="#3D4F66" />
              </View>
            </TouchableOpacity>

            {isExpanded && (
              <View className="ml-6 mb-2">
                {sys.biomarkers.map((bm, i) => (
                  <View key={i} className="flex-row items-center justify-between py-1">
                    <Text className="text-[#8B9BB4] text-xs flex-1">{bm.name}</Text>
                    <View className="flex-row items-center gap-2">
                      {bm.delta != null && (
                        <Text className="text-[10px]" style={{ color: bm.delta < 0 ? '#6EE7B7' : bm.delta > 0 ? '#F87171' : '#526380' }}>
                          {bm.delta > 0 ? '+' : ''}{bm.delta}
                        </Text>
                      )}
                      <Text className="text-xs font-sansMedium" style={{ color: BM_STATUS_COLORS[bm.status] ?? '#526380' }}>
                        {bm.value} {bm.unit}
                      </Text>
                      {bm.optimal_flag && (
                        <View className="bg-[#60A5FA15] rounded px-1">
                          <Text className="text-[#60A5FA] text-[8px]">not optimal</Text>
                        </View>
                      )}
                    </View>
                  </View>
                ))}
              </View>
            )}
          </View>
        );
      })}

      {/* HOMA-IR computed */}
      {homaIr != null && (
        <View className="mt-2 pt-2 border-t border-surface-border flex-row items-center justify-between">
          <View className="flex-row items-center gap-1.5">
            <Ionicons name="calculator-outline" size={12} color="#818CF8" />
            <Text className="text-[#8B9BB4] text-xs">HOMA-IR (computed)</Text>
          </View>
          <Text className="text-xs font-sansMedium" style={{
            color: homaIr < 1 ? '#6EE7B7' : homaIr < 2 ? '#8B9BB4' : homaIr < 3 ? '#F5A623' : '#F87171'
          }}>
            {homaIr} {homaIr < 1 ? '(optimal)' : homaIr < 2 ? '(normal)' : homaIr < 3 ? '(borderline)' : '(insulin resistant)'}
          </Text>
        </View>
      )}

      {/* Watch items */}
      {watchItems.length > 0 && (
        <View className="mt-2 pt-2 border-t border-surface-border">
          <Text className="text-[#F5A623] text-[10px] uppercase tracking-wider mb-1.5 font-sansMedium">Watch</Text>
          {watchItems.map((w, i) => (
            <View key={i} className="flex-row items-center gap-1.5 mb-1">
              <View className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: BM_STATUS_COLORS[w.status] }} />
              <Text className="text-[#8B9BB4] text-xs flex-1">
                {w.biomarker}: {w.value} {w.unit}{w.delta_text}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Doctor discussion */}
      {doctorDiscussion.length > 0 && (
        <View className="mt-2 pt-2 border-t border-surface-border">
          <TouchableOpacity
            onPress={() => setShowDoctor((s) => !s)}
            className="flex-row items-center justify-between"
            activeOpacity={0.7}
          >
            <Text className="text-[#00D4AA] text-[10px] uppercase tracking-wider font-sansMedium">
              Discuss With Your Doctor
            </Text>
            <Ionicons name={showDoctor ? 'chevron-up' : 'chevron-down'} size={12} color="#00D4AA" />
          </TouchableOpacity>
          {showDoctor && doctorDiscussion.map((d, i) => (
            <View key={i} className="mt-2 bg-white/3 rounded-lg p-2.5">
              <Text className="text-[#E8EDF5] text-xs font-sansMedium">{d.finding}</Text>
              <Text className="text-[#526380] text-[10px] mt-0.5 leading-4">{d.what_it_means}</Text>
              <Text className="text-[#00D4AA] text-[10px] mt-1">Ask: {d.what_to_ask}</Text>
              <Text className="text-[#3D4F66] text-[10px] mt-0.5">→ {d.follow_up}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}
