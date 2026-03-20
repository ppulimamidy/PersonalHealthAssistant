/**
 * Recommended Tests Card — standard screening + advanced biomarker suggestions.
 * Personalized by age, sex, conditions, and what the user has already tested.
 */

import { useState } from 'react';
import { View, Text, TouchableOpacity, Share } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface TestRec {
  test_name: string;
  category: string;
  system?: string;
  why?: string;
  who?: string;
  personalized_reason?: string;
  reason?: string;
  frequency: string;
  one_time?: boolean;
  ever_tested: boolean;
  priority: string;
}

interface Props {
  standard: TestRec[];
  advanced: TestRec[];
  conditions: string[];
  userProfile: string;
  onGenerateNote: () => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: '#F87171',
  medium: '#F5A623',
  low: '#526380',
};

function TestRow({ test }: Readonly<{ test: TestRec }>) {
  const [expanded, setExpanded] = useState(false);
  const dotColor = PRIORITY_COLORS[test.priority] ?? '#526380';

  return (
    <TouchableOpacity
      onPress={() => setExpanded((e) => !e)}
      className="py-2 border-b border-surface-border"
      activeOpacity={0.7}
    >
      <View className="flex-row items-center gap-2">
        <View className="w-2 h-2 rounded-full" style={{ backgroundColor: dotColor }} />
        <Text className="text-[#E8EDF5] text-sm flex-1 font-sansMedium">{test.test_name}</Text>
        {test.ever_tested ? (
          <View className="bg-[#6EE7B712] rounded px-1.5 py-0.5">
            <Text className="text-[#6EE7B7] text-[9px]">Tested</Text>
          </View>
        ) : (
          <View className="bg-[#F5A62312] rounded px-1.5 py-0.5">
            <Text className="text-[#F5A623] text-[9px]">Not tested</Text>
          </View>
        )}
        {test.one_time && (
          <View className="bg-white/5 rounded px-1.5 py-0.5">
            <Text className="text-[#3D4F66] text-[9px]">One-time</Text>
          </View>
        )}
      </View>

      <Text className="text-[#526380] text-[10px] mt-0.5 ml-4" numberOfLines={expanded ? undefined : 1}>
        {test.personalized_reason ?? test.reason ?? test.why ?? ''}
      </Text>

      {expanded && (
        <View className="ml-4 mt-1.5">
          {test.who && (
            <Text className="text-[#3D4F66] text-[10px]">Who should get it: {test.who}</Text>
          )}
          <Text className="text-[#3D4F66] text-[10px]">Frequency: {test.frequency}</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

export default function RecommendedTestsCard({ standard, advanced, conditions, userProfile, onGenerateNote }: Readonly<Props>) {
  const [showStandard, setShowStandard] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(true);

  const untestedAdvanced = advanced.filter((t) => !t.ever_tested);

  if (standard.length === 0 && advanced.length === 0) return null;

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Header */}
      <View className="flex-row items-center justify-between mb-3">
        <View className="flex-row items-center gap-2">
          <Ionicons name="flask-outline" size={14} color="#818CF8" />
          <Text className="text-[#526380] text-xs uppercase tracking-wider font-sansMedium">
            Recommended Tests
          </Text>
        </View>
        <Text className="text-[#3D4F66] text-[10px]">{userProfile}</Text>
      </View>

      {/* Advanced biomarkers (shown first — higher value) */}
      {advanced.length > 0 && (
        <View className="mb-2">
          <TouchableOpacity
            onPress={() => setShowAdvanced((s) => !s)}
            className="flex-row items-center justify-between mb-1"
            activeOpacity={0.7}
          >
            <View className="flex-row items-center gap-1.5">
              <Ionicons name="sparkles" size={12} color="#818CF8" />
              <Text className="text-[#818CF8] text-xs font-sansMedium">Ask Your Doctor About</Text>
              {untestedAdvanced.length > 0 && (
                <View className="bg-[#818CF820] rounded-full px-1.5 py-0.5">
                  <Text className="text-[#818CF8] text-[9px]">{untestedAdvanced.length} new</Text>
                </View>
              )}
            </View>
            <Ionicons name={showAdvanced ? 'chevron-up' : 'chevron-down'} size={12} color="#526380" />
          </TouchableOpacity>
          {showAdvanced && advanced.map((t, i) => <TestRow key={`adv-${i}`} test={t} />)}
        </View>
      )}

      {/* Standard screening */}
      {standard.length > 0 && (
        <View>
          <TouchableOpacity
            onPress={() => setShowStandard((s) => !s)}
            className="flex-row items-center justify-between mb-1"
            activeOpacity={0.7}
          >
            <View className="flex-row items-center gap-1.5">
              <Ionicons name="shield-checkmark-outline" size={12} color="#526380" />
              <Text className="text-[#526380] text-xs font-sansMedium">Standard Screening</Text>
            </View>
            <Ionicons name={showStandard ? 'chevron-up' : 'chevron-down'} size={12} color="#526380" />
          </TouchableOpacity>
          {showStandard && standard.map((t, i) => <TestRow key={`std-${i}`} test={t} />)}
        </View>
      )}

      {/* Generate doctor note */}
      <TouchableOpacity
        onPress={onGenerateNote}
        className="mt-3 flex-row items-center justify-center gap-1.5 py-2 rounded-lg"
        style={{ backgroundColor: '#00D4AA12', borderWidth: 1, borderColor: '#00D4AA25' }}
        activeOpacity={0.7}
      >
        <Ionicons name="document-text-outline" size={14} color="#00D4AA" />
        <Text className="text-[#00D4AA] text-xs font-sansMedium">Generate note for your doctor</Text>
      </TouchableOpacity>
    </View>
  );
}
