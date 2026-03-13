import { View, Text, Switch, TouchableOpacity, ScrollView } from 'react-native';
import { useState } from 'react';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function SettingsScreen() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  return (
    <View className="flex-1 bg-obsidian-900">
      <View className="px-6 pt-14 pb-4 flex-row items-center">
        <TouchableOpacity onPress={() => router.back()} className="mr-3">
          <Ionicons name="arrow-back" size={22} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-2xl font-display text-[#E8EDF5]">Settings</Text>
      </View>

      <ScrollView className="flex-1 px-6">
        <Text className="text-[#526380] text-xs uppercase tracking-widest mb-3">Notifications</Text>
        <View className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 flex-row items-center justify-between mb-6">
          <View>
            <Text className="text-[#E8EDF5]">Push Notifications</Text>
            <Text className="text-[#526380] text-sm">Medication reminders, check-in prompts</Text>
          </View>
          <Switch
            value={notificationsEnabled}
            onValueChange={setNotificationsEnabled}
            trackColor={{ false: '#232C3A', true: '#00D4AA40' }}
            thumbColor={notificationsEnabled ? '#00D4AA' : '#526380'}
          />
        </View>

        <Text className="text-[#526380] text-xs uppercase tracking-widest mb-3">About</Text>
        <View className="bg-surface-raised border border-surface-border rounded-xl overflow-hidden mb-6">
          {[
            { label: 'Version', value: '1.0.0 (Phase 0 Scaffold)' },
            { label: 'API', value: process.env.EXPO_PUBLIC_API_URL ?? 'localhost:8100' },
          ].map(({ label, value }, i, arr) => (
            <View
              key={label}
              className={`flex-row items-center justify-between px-4 py-3 ${i < arr.length - 1 ? 'border-b border-surface-border' : ''}`}
            >
              <Text className="text-[#E8EDF5]">{label}</Text>
              <Text className="text-[#526380] text-sm">{value}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}
