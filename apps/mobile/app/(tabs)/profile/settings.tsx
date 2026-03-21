import { useState } from 'react';
import {
  View, Text, Switch, TouchableOpacity, ScrollView,
  TextInput, ActivityIndicator, Alert, Platform,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import * as Haptics from 'expo-haptics';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';

// Capabilities map to user_role in DB for backward compatibility

function SectionLabel({ children }: Readonly<{ children: string }>) {
  return (
    <Text className="text-[#526380] text-xs uppercase tracking-widest mb-3 mt-6">{children}</Text>
  );
}

function SettingsRow({
  icon, label, value, onPress, destructive, rightElement,
}: Readonly<{
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  value?: string;
  onPress?: () => void;
  destructive?: boolean;
  rightElement?: React.ReactNode;
}>) {
  const labelColor = destructive ? '#F87171' : '#E8EDF5';
  const iconColor  = destructive ? '#F87171' : '#526380';
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={!onPress && !rightElement}
      className="flex-row items-center px-4 py-3.5 border-b border-surface-border"
      activeOpacity={onPress ? 0.7 : 1}
    >
      <Ionicons name={icon} size={18} color={iconColor} style={{ marginRight: 12, width: 20 }} />
      <Text className="flex-1 font-sansMedium" style={{ color: labelColor }}>{label}</Text>
      {value ? <Text className="text-[#526380] text-sm mr-2">{value}</Text> : null}
      {rightElement ?? (onPress != null ? <Ionicons name="chevron-forward" size={16} color="#3A4A5C" /> : null)}
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  // Profile edit state
  const [editingProfile, setEditingProfile] = useState(false);
  const [editWeight, setEditWeight] = useState('');
  const [editHeight, setEditHeight] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);

  // Notification state
  const [notifEnabled, setNotifEnabled]   = useState(true);
  const [togglingNotif, setTogglingNotif] = useState(false);

  // Role saving
  const [savingRole, setSavingRole] = useState(false);

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const { data } = await api.get('/api/v1/profile/checkin');
      return data;
    },
  });

  const currentRole: string = profile?.user_role ?? 'patient';
  const displayName = (user?.user_metadata?.full_name as string | undefined) ?? user?.email ?? 'User';
  const appVersion: string = Constants.expoConfig?.version ?? '1.0.0';

  function openEditProfile() {
    setEditWeight(profile?.weight_kg ? String(profile.weight_kg) : '');
    setEditHeight(profile?.height_cm ? String(profile.height_cm) : '');
    setEditingProfile(true);
  }

  async function saveProfile() {
    setSavingProfile(true);
    try {
      await api.patch('/api/v1/profile/checkin', {
        weight_kg: editWeight ? Number.parseFloat(editWeight) : undefined,
        height_cm: editHeight ? Number.parseFloat(editHeight) : undefined,
      });
      await queryClient.invalidateQueries({ queryKey: ['profile'] });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setEditingProfile(false);
    } catch {
      Alert.alert('Error', 'Could not save profile changes.');
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleRoleChange(newRole: 'patient' | 'provider' | 'caregiver') {
    if (newRole === currentRole || savingRole) return;
    setSavingRole(true);
    try {
      await api.patch('/api/v1/profile/role', { user_role: newRole });
      await queryClient.invalidateQueries({ queryKey: ['profile'] });
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch {
      Alert.alert('Error', 'Could not update role.');
    } finally {
      setSavingRole(false);
    }
  }

  async function toggleNotifications(value: boolean) {
    setTogglingNotif(true);
    try {
      if (value) {
        const { status } = await Notifications.requestPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert(
            'Notifications Blocked',
            'Enable notifications in iOS Settings → Vitalix → Notifications.',
          );
          setTogglingNotif(false);
          return;
        }
      }
      setNotifEnabled(value);
    } finally {
      setTogglingNotif(false);
    }
  }

  return (
    <View className="flex-1 bg-obsidian-900">
      {/* Header */}
      <View className="px-6 pt-14 pb-4 flex-row items-center border-b border-surface-border">
        <TouchableOpacity onPress={() => router.back()} className="mr-3 p-1">
          <Ionicons name="arrow-back" size={22} color="#E8EDF5" />
        </TouchableOpacity>
        <Text className="text-2xl font-display text-[#E8EDF5] flex-1">Settings</Text>
      </View>

      <ScrollView className="flex-1" contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 48 }}>

        {/* ── Profile ── */}
        <SectionLabel>Profile</SectionLabel>
        <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden">
          {editingProfile ? (
            <View className="p-4 gap-3">
              <View>
                <Text className="text-[#526380] text-xs mb-1">Weight (kg)</Text>
                <TextInput
                  className="bg-obsidian-900 border border-surface-border rounded-xl px-4 py-2.5 text-[#E8EDF5]"
                  value={editWeight}
                  onChangeText={setEditWeight}
                  keyboardType="decimal-pad"
                  placeholder="70"
                  placeholderTextColor="#526380"
                />
              </View>
              <View>
                <Text className="text-[#526380] text-xs mb-1">Height (cm)</Text>
                <TextInput
                  className="bg-obsidian-900 border border-surface-border rounded-xl px-4 py-2.5 text-[#E8EDF5]"
                  value={editHeight}
                  onChangeText={setEditHeight}
                  keyboardType="decimal-pad"
                  placeholder="170"
                  placeholderTextColor="#526380"
                />
              </View>
              <View className="flex-row gap-2 mt-1">
                <TouchableOpacity
                  onPress={() => setEditingProfile(false)}
                  className="flex-1 py-2.5 rounded-xl border border-surface-border items-center"
                >
                  <Text className="text-[#526380] font-sansMedium text-sm">Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={saveProfile}
                  disabled={savingProfile}
                  className="flex-1 py-2.5 rounded-xl bg-primary-500 items-center"
                >
                  {savingProfile
                    ? <ActivityIndicator size="small" color="#080B10" />
                    : <Text className="text-obsidian-900 font-sansMedium text-sm">Save</Text>}
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <>
              <SettingsRow icon="person-outline"  label="Name"   value={displayName} />
              <SettingsRow icon="mail-outline"    label="Email"  value={user?.email ?? '—'} />
              {profile?.weight_kg && (
                <SettingsRow icon="barbell-outline" label="Weight" value={`${profile.weight_kg} kg`} />
              )}
              {profile?.height_cm && (
                <SettingsRow icon="resize-outline"  label="Height" value={`${profile.height_cm} cm`} />
              )}
              <SettingsRow icon="pencil-outline"  label="Edit Profile" onPress={openEditProfile} />
            </>
          )}
        </View>

        {/* ── Account Capabilities ── */}
        <SectionLabel>Account Capabilities</SectionLabel>
        <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden">
          {/* Personal — always on */}
          <View className="flex-row items-center px-4 py-3.5 border-b border-surface-border">
            <Ionicons name="person-outline" size={18} color="#00D4AA" style={{ marginRight: 12, width: 20 }} />
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium">Personal Health Tracking</Text>
              <Text className="text-[#526380] text-[10px] mt-0.5">Track your sleep, nutrition, medications, labs & symptoms</Text>
            </View>
            <View className="bg-[#00D4AA20] rounded-full px-2 py-0.5">
              <Text className="text-[#00D4AA] text-[10px] font-sansMedium">Always on</Text>
            </View>
          </View>

          {/* Patient Monitoring (Provider) */}
          <View className="flex-row items-center px-4 py-3.5 border-b border-surface-border">
            <Ionicons name="medical-outline" size={18} color="#818CF8" style={{ marginRight: 12, width: 20 }} />
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium">Patient Monitoring</Text>
              <Text className="text-[#526380] text-[10px] mt-0.5">View health data shared by your patients</Text>
            </View>
            {savingRole ? (
              <ActivityIndicator size="small" color="#818CF8" />
            ) : (
              <Switch
                value={currentRole === 'provider'}
                onValueChange={(on) => handleRoleChange(on ? 'provider' : 'patient')}
                trackColor={{ false: '#232C3A', true: '#818CF840' }}
                thumbColor={currentRole === 'provider' ? '#818CF8' : '#526380'}
              />
            )}
          </View>

          {/* Family Caregiving */}
          <View className="flex-row items-center px-4 py-3.5">
            <Ionicons name="people-outline" size={18} color="#EC4899" style={{ marginRight: 12, width: 20 }} />
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium">Family Caregiving</Text>
              <Text className="text-[#526380] text-[10px] mt-0.5">Monitor family members' health & sharing</Text>
            </View>
            {savingRole ? (
              <ActivityIndicator size="small" color="#EC4899" />
            ) : (
              <Switch
                value={currentRole === 'caregiver'}
                onValueChange={(on) => handleRoleChange(on ? 'caregiver' : 'patient')}
                trackColor={{ false: '#232C3A', true: '#EC489940' }}
                thumbColor={currentRole === 'caregiver' ? '#EC4899' : '#526380'}
              />
            )}
          </View>
        </View>
        <Text className="text-[#3D4F66] text-[10px] mt-2 px-1">
          Your personal health data is always available regardless of which capabilities you enable.
        </Text>

        {/* ── Notifications ── */}
        <SectionLabel>Notifications</SectionLabel>
        <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden">
          <View className="flex-row items-center px-4 py-3.5">
            <Ionicons name="notifications-outline" size={18} color="#526380" style={{ marginRight: 12, width: 20 }} />
            <View className="flex-1">
              <Text className="text-[#E8EDF5] font-sansMedium">Push Notifications</Text>
              <Text className="text-[#526380] text-xs mt-0.5">Medication reminders, check-in prompts</Text>
            </View>
            {togglingNotif ? (
              <ActivityIndicator size="small" color="#00D4AA" />
            ) : (
              <Switch
                value={notifEnabled}
                onValueChange={toggleNotifications}
                trackColor={{ false: '#232C3A', true: '#00D4AA40' }}
                thumbColor={notifEnabled ? '#00D4AA' : '#526380'}
              />
            )}
          </View>
        </View>

        {/* ── Data ── */}
        <SectionLabel>Data & Privacy</SectionLabel>
        <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden">
          <SettingsRow
            icon="download-outline"
            label="Export Health Data"
            value="PDF"
            onPress={() => Alert.alert('Coming Soon', 'Data export will be available in a future update.')}
          />
          <SettingsRow
            icon="lock-closed-outline"
            label="Privacy & Security"
            onPress={() => Alert.alert(
              'Privacy & Security',
              'Your data is encrypted at rest and in transit.\n\nVitalix is HIPAA-aware and does not sell your health data.\n\nManage data sharing in Profile → Care Team Sharing.',
            )}
          />
        </View>

        {/* ── Referral ── */}
        <SectionLabel>Share Vitalix</SectionLabel>
        <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden">
          <SettingsRow
            icon="gift-outline"
            label="Invite Friends"
            onPress={() => Alert.alert('Coming Soon', 'Referral program launching soon.')}
          />
        </View>

        {/* ── Security ── */}
        <SectionLabel>Security</SectionLabel>
        <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden">
          <SettingsRow
            icon="key-outline"
            label="Two-Factor Authentication"
            value="Set Up"
            onPress={() => Alert.alert(
              'Two-Factor Authentication',
              'To set up 2FA with an authenticator app, visit the web dashboard at app.vitalix.health → Settings → Two-Factor Authentication.\n\nThis adds an extra layer of security to protect your health data.',
            )}
          />
        </View>

        {/* ── About ── */}
        <SectionLabel>About</SectionLabel>
        <View className="bg-surface-raised border border-surface-border rounded-2xl overflow-hidden">
          <SettingsRow icon="information-circle-outline" label="Version"     value={appVersion} />
          <SettingsRow icon="globe-outline"              label="Platform"    value={`${Platform.OS} ${Platform.Version}`} />
          <SettingsRow
            icon="document-text-outline"
            label="Terms of Service"
            onPress={() => Alert.alert('Terms of Service', 'Visit vitalix.app/terms')}
          />
          <SettingsRow
            icon="shield-checkmark-outline"
            label="Privacy Policy"
            onPress={() => Alert.alert('Privacy Policy', 'Visit vitalix.app/privacy')}
          />
        </View>

        {/* ── Danger Zone ── */}
        <SectionLabel>Danger Zone</SectionLabel>
        <View className="bg-surface-raised border border-red-500/30 rounded-2xl overflow-hidden">
          <SettingsRow
            icon="trash-outline"
            label="Delete Account"
            onPress={() => {
              Alert.alert(
                'Delete Account',
                'This will permanently delete your account and ALL health data (medications, labs, symptoms, meals, devices, insights). This cannot be undone.',
                [
                  { text: 'Cancel', style: 'cancel' },
                  {
                    text: 'Delete Everything',
                    style: 'destructive',
                    onPress: () => {
                      Alert.alert(
                        'Final Confirmation',
                        'Are you absolutely sure? All your data will be permanently erased.',
                        [
                          { text: 'Cancel', style: 'cancel' },
                          {
                            text: 'Yes, Delete My Account',
                            style: 'destructive',
                            onPress: async () => {
                              try {
                                await api.delete('/api/v1/profile/account');
                                Alert.alert('Account Deleted', 'Your account and all data have been permanently deleted.');
                                const { signOut } = useAuthStore.getState();
                                signOut();
                              } catch {
                                Alert.alert('Error', 'Failed to delete account. Please try again or contact support.');
                              }
                            },
                          },
                        ]
                      );
                    },
                  },
                ]
              );
            }}
          />
        </View>

        <Text className="text-[#3A4A5C] text-[10px] text-center mt-4 mb-2 px-4">
          Data Retention: Your data is kept while your account is active. Inactive accounts (no login for 24 months) receive warnings before archival. Export or delete anytime.
        </Text>

      </ScrollView>
    </View>
  );
}
