/**
 * Interaction Alert Card — drug-drug, drug-nutrient, and drug-food
 * interaction warnings with lab cross-reference.
 */

import { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface DrugNutrient {
  medication: string;
  depletes: string;
  covered_by_supplement: boolean;
  lab_status: string | null;
  lab_value: number | null;
  severity: string;
  note: string;
}

interface DrugFood {
  medication: string;
  food: string;
  severity: string;
  note: string;
}

interface DrugDrug {
  med_a: string;
  med_b: string;
  severity: string;
  note: string;
}

interface Props {
  drugNutrient: DrugNutrient[];
  drugFood: DrugFood[];
  drugDrug: DrugDrug[];
  onAddSupplement?: (nutrient: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  high: '#F87171',
  major: '#F87171',
  moderate: '#F5A623',
  medium: '#F5A623',
  minor: '#526380',
  low: '#526380',
};

export default function InteractionAlertCard({ drugNutrient, drugFood, drugDrug, onAddSupplement }: Readonly<Props>) {
  const [expanded, setExpanded] = useState(false);
  const totalAlerts = drugNutrient.length + drugFood.length + drugDrug.length;

  if (totalAlerts === 0) return null;

  const highPriority = drugNutrient.filter((d) => d.severity === 'high' && !d.covered_by_supplement);

  return (
    <View className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3">
      <TouchableOpacity
        onPress={() => setExpanded((e) => !e)}
        className="flex-row items-center justify-between"
        activeOpacity={0.7}
      >
        <View className="flex-row items-center gap-2">
          <Ionicons name="warning-outline" size={14} color="#F5A623" />
          <Text className="text-[#F5A623] text-xs uppercase tracking-wider font-sansMedium">
            Interaction Alerts
          </Text>
          <View className="bg-[#F5A62320] rounded-full px-1.5 py-0.5">
            <Text className="text-[#F5A623] text-[9px] font-sansMedium">{totalAlerts}</Text>
          </View>
        </View>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={14} color="#526380" />
      </TouchableOpacity>

      {/* Always show high-priority nutrient depletions */}
      {!expanded && highPriority.length > 0 && (
        <View className="mt-2">
          {highPriority.slice(0, 2).map((d, i) => (
            <View key={`hp-${i}`} className="flex-row items-center gap-1.5 mb-1">
              <View className="w-1.5 h-1.5 rounded-full bg-[#F87171]" />
              <Text className="text-[#8B9BB4] text-xs flex-1" numberOfLines={1}>
                {d.medication} depletes {d.depletes}
                {d.lab_status ? ` (labs: ${d.lab_status})` : ''}
              </Text>
            </View>
          ))}
        </View>
      )}

      {expanded && (
        <View className="mt-3">
          {/* Drug-nutrient depletions */}
          {drugNutrient.length > 0 && (
            <View className="mb-3">
              <Text className="text-[#526380] text-[10px] uppercase tracking-wider mb-1.5">Nutrient Depletions</Text>
              {drugNutrient.map((d, i) => {
                const color = SEVERITY_COLORS[d.severity] ?? '#526380';
                return (
                  <View key={`dn-${i}`} className="mb-2 rounded-lg p-2.5" style={{ backgroundColor: `${color}08` }}>
                    <View className="flex-row items-center justify-between mb-0.5">
                      <Text className="text-[#E8EDF5] text-xs font-sansMedium">
                        {d.medication} → depletes {d.depletes}
                      </Text>
                      <View className="flex-row items-center gap-1">
                        {d.covered_by_supplement ? (
                          <View className="bg-[#6EE7B712] rounded px-1.5 py-0.5">
                            <Text className="text-[#6EE7B7] text-[9px]">Covered</Text>
                          </View>
                        ) : (
                          <View className="bg-[#F8717112] rounded px-1.5 py-0.5">
                            <Text className="text-[#F87171] text-[9px]">Gap</Text>
                          </View>
                        )}
                      </View>
                    </View>
                    <Text className="text-[#526380] text-[10px] leading-4">{d.note}</Text>
                    {d.lab_status && (
                      <Text className="text-[10px] mt-0.5" style={{ color }}>
                        Lab: {d.depletes} is {d.lab_status}{d.lab_value != null ? ` (${d.lab_value})` : ''}
                      </Text>
                    )}
                    {!d.covered_by_supplement && onAddSupplement && (
                      <TouchableOpacity
                        onPress={() => onAddSupplement(d.depletes)}
                        className="mt-1.5 self-start flex-row items-center gap-1"
                        activeOpacity={0.7}
                      >
                        <Ionicons name="add-circle-outline" size={12} color="#00D4AA" />
                        <Text className="text-[#00D4AA] text-[10px] font-sansMedium">Add {d.depletes} supplement</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                );
              })}
            </View>
          )}

          {/* Drug-food interactions */}
          {drugFood.length > 0 && (
            <View className="mb-3">
              <Text className="text-[#526380] text-[10px] uppercase tracking-wider mb-1.5">Food Interactions</Text>
              {drugFood.map((d, i) => {
                const color = SEVERITY_COLORS[d.severity] ?? '#526380';
                return (
                  <View key={`df-${i}`} className="flex-row items-start gap-2 mb-1.5">
                    <View className="w-1.5 h-1.5 rounded-full mt-1.5" style={{ backgroundColor: color }} />
                    <View className="flex-1">
                      <Text className="text-[#E8EDF5] text-xs">{d.medication} + {d.food}</Text>
                      <Text className="text-[#526380] text-[10px]">{d.note}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          )}

          {/* Drug-drug interactions */}
          {drugDrug.length > 0 && (
            <View>
              <Text className="text-[#526380] text-[10px] uppercase tracking-wider mb-1.5">Timing Conflicts</Text>
              {drugDrug.map((d, i) => (
                <View key={`dd-${i}`} className="flex-row items-start gap-2 mb-1.5">
                  <View className="w-1.5 h-1.5 rounded-full mt-1.5 bg-[#F5A623]" />
                  <View className="flex-1">
                    <Text className="text-[#E8EDF5] text-xs">{d.med_a} + {d.med_b}</Text>
                    <Text className="text-[#526380] text-[10px]">{d.note}</Text>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
    </View>
  );
}
