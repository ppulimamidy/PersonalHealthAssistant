import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const LOG_OPTIONS = [
  { label: 'Log Symptom',   icon: 'thermometer-outline' as const,  route: '/(tabs)/log/symptoms',       description: 'Record how you feel' },
  { label: 'Medications',   icon: 'medical-outline' as const,       route: '/(tabs)/log/medications',    description: 'Track adherence & schedule' },
  { label: 'Nutrition',     icon: 'restaurant-outline' as const,    route: '/(tabs)/log/nutrition',      description: 'Log meals & food intake' },
  { label: 'Lab Results',   icon: 'flask-outline' as const,         route: '/(tabs)/log/lab-results',    description: 'Record blood work & tests' },
  { label: 'Medical Records', icon: 'document-text-outline' as const, route: '/(tabs)/log/medical-records', description: 'Pathology, genomic & imaging' },
  { label: 'Experiments',   icon: 'flask-outline' as const,         route: '/(tabs)/log/interventions',  description: 'Track what you\'re trying' },
];

export default function LogHubScreen() {
  return (
    <View className="flex-1 bg-obsidian-900">
      <View className="px-6 pt-14 pb-6">
        <Text className="text-2xl font-display text-[#E8EDF5]">Log</Text>
        <Text className="text-[#526380] mt-1">Record your health data</Text>
      </View>
      <ScrollView className="flex-1 px-6">
        {LOG_OPTIONS.map((opt) => (
          <TouchableOpacity
            key={opt.label}
            onPress={() => router.push(opt.route as never)}
            className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl p-4 mb-3"
            activeOpacity={0.7}
          >
            <View className="bg-primary-500/10 rounded-xl p-3 mr-4">
              <Ionicons name={opt.icon} size={24} color="#00D4AA" />
            </View>
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium">{opt.label}</Text>
              <Text className="text-[#526380] text-sm mt-0.5">{opt.description}</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color="#526380" />
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}
