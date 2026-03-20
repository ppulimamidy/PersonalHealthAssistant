/**
 * Treatment Overview Card — persistent card at top of medications screen
 * showing adherence, lab validation, interaction alerts, and AI summary.
 */

import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  adherence: { rate_pct: number; taken_today: number; total_today: number };
  labValidation: { improving: number; monitoring: number };
  supplementGaps: number;
  interactionAlerts: number;
  aiSummary: string;
}

export default function TreatmentOverviewCard({
  adherence, labValidation, supplementGaps, interactionAlerts, aiSummary,
}: Readonly<Props>) {
  const adherenceColor = adherence.rate_pct >= 90 ? '#6EE7B7' : adherence.rate_pct >= 70 ? '#F5A623' : '#F87171';

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      {/* Header row */}
      <View className="flex-row items-center gap-2 mb-3">
        <Ionicons name="shield-checkmark-outline" size={14} color="#00D4AA" />
        <Text className="text-[#526380] text-xs uppercase tracking-wider font-sansMedium">Treatment Overview</Text>
      </View>

      {/* Stats row */}
      <View className="flex-row gap-2 mb-3">
        {/* Adherence */}
        <View className="flex-1 bg-white/3 rounded-lg p-2 items-center">
          <Text className="font-display text-lg" style={{ color: adherenceColor }}>{adherence.rate_pct}%</Text>
          <Text className="text-[#526380] text-[9px]">Adherence</Text>
        </View>
        {/* Lab evidence */}
        <View className="flex-1 bg-white/3 rounded-lg p-2 items-center">
          <Text className="font-display text-lg text-[#6EE7B7]">{labValidation.improving}</Text>
          <Text className="text-[#526380] text-[9px]">Lab proven</Text>
        </View>
        {/* Alerts */}
        <View className="flex-1 bg-white/3 rounded-lg p-2 items-center">
          <Text className="font-display text-lg" style={{ color: interactionAlerts > 0 ? '#F5A623' : '#526380' }}>
            {interactionAlerts}
          </Text>
          <Text className="text-[#526380] text-[9px]">Alerts</Text>
        </View>
        {/* Gaps */}
        <View className="flex-1 bg-white/3 rounded-lg p-2 items-center">
          <Text className="font-display text-lg" style={{ color: supplementGaps > 0 ? '#F87171' : '#526380' }}>
            {supplementGaps}
          </Text>
          <Text className="text-[#526380] text-[9px]">Gaps</Text>
        </View>
      </View>

      {/* AI summary */}
      <Text className="text-[#8B9BB4] text-sm leading-5" style={{ fontStyle: 'italic' }}>
        {aiSummary}
      </Text>
    </View>
  );
}
