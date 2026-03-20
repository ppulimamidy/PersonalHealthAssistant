/**
 * Lab Insight Card — appears after uploading lab results.
 * Shows AI analysis referencing medications, supplements, conditions.
 */

import { useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface SupplementGap {
  biomarker: string;
  status: string;
  value: number;
  unit: string;
  suggested_supplement: string;
  reason: string;
}

interface Props {
  insight: string;
  headline: string;
  abnormalCount: number;
  biomarkerCount: number;
  supplementGaps: SupplementGap[];
  quickActions: string[];
  onAction: (action: string) => void;
  onDismiss: () => void;
}

export default function LabInsightCard({
  insight, headline, abnormalCount, biomarkerCount, supplementGaps, quickActions, onAction, onDismiss,
}: Readonly<Props>) {
  const slideAnim = useRef(new Animated.Value(80)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(slideAnim, { toValue: 0, useNativeDriver: true, tension: 50, friction: 9 }),
      Animated.timing(fadeAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  const statusColor = abnormalCount === 0 ? '#6EE7B7' : abnormalCount <= 2 ? '#F5A623' : '#F87171';

  return (
    <Animated.View
      style={{ transform: [{ translateY: slideAnim }], opacity: fadeAnim }}
      className="bg-surface-raised border border-surface-border rounded-2xl p-4 mb-3"
    >
      <TouchableOpacity onPress={onDismiss} className="absolute top-3 right-3 z-10" hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
        <Ionicons name="close" size={16} color="#526380" />
      </TouchableOpacity>

      {/* Header */}
      <View className="flex-row items-center gap-2 mb-2">
        <View className="w-2 h-2 rounded-full" style={{ backgroundColor: statusColor }} />
        <Text className="text-[#E8EDF5] text-sm font-sansMedium">{headline}</Text>
      </View>

      {/* AI insight */}
      <Text className="text-[#8B9BB4] text-sm leading-5 mb-3" style={{ fontStyle: 'italic' }}>
        {insight}
      </Text>

      {/* Supplement gaps */}
      {supplementGaps.length > 0 && (
        <View className="mb-3">
          {supplementGaps.map((gap, i) => (
            <View key={i} className="flex-row items-center gap-2 mb-1 bg-[#F5A62310] rounded-lg px-3 py-1.5">
              <Ionicons name="alert-circle-outline" size={14} color="#F5A623" />
              <Text className="text-[#F5A623] text-xs flex-1">
                Low {gap.biomarker} — no {gap.suggested_supplement} supplement
              </Text>
              <TouchableOpacity
                onPress={() => onAction(`add_supplement:${gap.suggested_supplement}`)}
                hitSlop={{ top: 6, bottom: 6, left: 6, right: 6 }}
              >
                <Text className="text-[#00D4AA] text-[10px] font-sansMedium">Add</Text>
              </TouchableOpacity>
            </View>
          ))}
        </View>
      )}

      {/* Quick action chips */}
      <View className="flex-row flex-wrap gap-2">
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action}
            onPress={() => onAction(action)}
            className="flex-row items-center gap-1 px-3 py-1.5 rounded-lg"
            style={{ backgroundColor: '#00D4AA15', borderWidth: 1, borderColor: '#00D4AA30' }}
            activeOpacity={0.7}
          >
            <Ionicons
              name={
                action === 'Adjust supplements' ? 'flask-outline' as never :
                action === 'Share with doctor' ? 'document-text-outline' as never :
                'alarm-outline' as never
              }
              size={12}
              color="#00D4AA"
            />
            <Text className="text-[#00D4AA] text-xs font-sansMedium">{action}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </Animated.View>
  );
}
