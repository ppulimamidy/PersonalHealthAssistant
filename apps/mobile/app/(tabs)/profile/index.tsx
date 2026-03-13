import { View, Text, ScrollView, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/stores/authStore';
import { supabase } from '@/lib/supabase';
import { unregisterPushToken } from '@/services/notifications';

function ProfileRow({ icon, label, onPress }: { icon: React.ComponentProps<typeof Ionicons>['name']; label: string; onPress: () => void }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      className="flex-row items-center bg-surface-raised border border-surface-border rounded-xl p-4 mb-2"
      activeOpacity={0.7}
    >
      <Ionicons name={icon} size={20} color="#526380" className="mr-3" />
      <Text className="text-[#E8EDF5] flex-1 ml-3">{label}</Text>
      <Ionicons name="chevron-forward" size={16} color="#526380" />
    </TouchableOpacity>
  );
}

export default function ProfileScreen() {
  const { user, profile, logout } = useAuthStore();
  const name = (user?.user_metadata?.full_name as string | undefined) ?? user?.email ?? 'User';

  async function handleLogout() {
    await unregisterPushToken();
    await supabase.auth.signOut();
    logout();
    router.replace('/(auth)/login');
  }

  return (
    <ScrollView className="flex-1 bg-obsidian-900" contentContainerStyle={{ padding: 24, paddingTop: 56 }}>
      {/* Avatar */}
      <View className="items-center mb-8">
        <View className="w-20 h-20 rounded-full bg-primary-500/20 border border-primary-500/40 items-center justify-center mb-3">
          <Text className="text-primary-500 text-3xl font-display">{name[0]?.toUpperCase()}</Text>
        </View>
        <Text className="text-[#E8EDF5] text-lg font-sansMedium">{name}</Text>
        <Text className="text-[#526380] text-sm mt-1">{user?.email}</Text>
      </View>

      <ProfileRow icon="fitness-outline" label="Health Profile" onPress={() => router.push('/(tabs)/profile/health')} />
      <ProfileRow icon="phone-portrait-outline" label="Devices & Health Sync" onPress={() => router.push('/(tabs)/profile/devices')} />
      <ProfileRow icon="card-outline" label="Plan & Billing" onPress={() => router.push('/(tabs)/profile/billing')} />
      <ProfileRow icon="body-outline" label="Health Twin" onPress={() => router.push('/(tabs)/profile/health-twin')} />
      <ProfileRow icon="library-outline" label="Research" onPress={() => router.push('/(tabs)/profile/research')} />
      <ProfileRow icon="share-social-outline" label="Care Team Sharing" onPress={() => router.push('/(tabs)/profile/sharing' as never)} />
      <ProfileRow icon="people-outline" label="Patients" onPress={() => router.push('/(tabs)/profile/patients' as never)} />
      <ProfileRow icon="settings-outline" label="Settings" onPress={() => router.push('/(tabs)/profile/settings')} />

      <View className="mt-6">
        <TouchableOpacity
          onPress={handleLogout}
          className="bg-health-critical/10 border border-health-critical/30 rounded-xl py-4 items-center"
          activeOpacity={0.8}
        >
          <Text className="text-health-critical font-sansMedium">Sign Out</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}
