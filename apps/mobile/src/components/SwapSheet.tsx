/**
 * Swap Sheet — shows 3 food alternatives based on health context.
 * Appears as a bottom sheet when user taps swap icon on a food item.
 */

import { View, Text, TouchableOpacity, ActivityIndicator, Modal } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Alternative {
  name: string;
  portion?: string;
  macros?: { calories: number; protein_g: number; carbs_g: number; fat_g: number };
  why?: string;
}

interface Props {
  visible: boolean;
  original: string;
  alternatives: Alternative[];
  loading: boolean;
  onSelect: (alt: Alternative) => void;
  onClose: () => void;
  onAskCoach: () => void;
}

export default function SwapSheet({ visible, original, alternatives, loading, onSelect, onClose, onAskCoach }: Readonly<Props>) {
  return (
    <Modal visible={visible} animationType="slide" transparent>
      <TouchableOpacity
        className="flex-1 bg-black/50"
        activeOpacity={1}
        onPress={onClose}
      />
      <View className="bg-[#0F1720] rounded-t-2xl px-5 pt-4 pb-8 border-t border-surface-border">
        {/* Header */}
        <View className="flex-row items-center justify-between mb-4">
          <View>
            <Text className="text-[#526380] text-xs uppercase tracking-wider">Swap</Text>
            <Text className="text-[#E8EDF5] font-sansMedium text-base">{original}</Text>
          </View>
          <TouchableOpacity onPress={onClose} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Ionicons name="close" size={20} color="#526380" />
          </TouchableOpacity>
        </View>

        {loading ? (
          <View className="items-center py-8">
            <ActivityIndicator color="#00D4AA" />
            <Text className="text-[#526380] text-xs mt-2">Finding alternatives...</Text>
          </View>
        ) : alternatives.length === 0 ? (
          <View className="items-center py-8">
            <Ionicons name="swap-horizontal-outline" size={32} color="#526380" />
            <Text className="text-[#526380] text-sm mt-2">No alternatives found</Text>
          </View>
        ) : (
          <View className="gap-2">
            {alternatives.map((alt, i) => (
              <TouchableOpacity
                key={i}
                onPress={() => onSelect(alt)}
                className="bg-surface-raised border border-surface-border rounded-xl p-3"
                activeOpacity={0.7}
              >
                <View className="flex-row items-center justify-between mb-1">
                  <Text className="text-[#E8EDF5] font-sansMedium text-sm flex-1">{alt.name}</Text>
                  {alt.portion && (
                    <Text className="text-[#526380] text-xs ml-2">{alt.portion}</Text>
                  )}
                </View>
                {alt.macros && (
                  <View className="flex-row gap-3 mb-1">
                    <Text className="text-[#8B9BB4] text-[10px]">{Math.round(alt.macros.calories)} cal</Text>
                    <Text className="text-[#6EE7B7] text-[10px]">P {Math.round(alt.macros.protein_g)}g</Text>
                    <Text className="text-[#60A5FA] text-[10px]">C {Math.round(alt.macros.carbs_g)}g</Text>
                    <Text className="text-[#F5A623] text-[10px]">F {Math.round(alt.macros.fat_g)}g</Text>
                  </View>
                )}
                {alt.why && (
                  <Text className="text-[#526380] text-xs leading-4" numberOfLines={2}>{alt.why}</Text>
                )}
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Bottom actions */}
        <TouchableOpacity
          onPress={onAskCoach}
          className="mt-3 flex-row items-center justify-center gap-1.5 py-2"
          activeOpacity={0.7}
        >
          <Ionicons name="chatbubble-outline" size={14} color="#00D4AA" />
          <Text className="text-[#00D4AA] text-xs font-sansMedium">Ask nutrition coach instead</Text>
        </TouchableOpacity>
      </View>
    </Modal>
  );
}
