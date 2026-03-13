import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { Link, router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { supabase } from '@/lib/supabase';
import { useAuthStore } from '@/stores/authStore';
import { registerForPushNotifications } from '@/services/notifications';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setUser } = useAuthStore();

  async function handleLogin() {
    if (!email || !password) {
      setError('Email and password are required');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });
      if (authError) throw authError;
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setUser(data.user);
      // Register push token in background — non-blocking
      registerForPushNotifications().catch(() => {});
      router.replace('/(tabs)/home');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      setError(msg);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-obsidian-900"
    >
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
      >
        <View className="flex-1 justify-center px-6 py-12">
          {/* Logo / Brand */}
          <View className="mb-10">
            <Text className="text-4xl font-display text-primary-500 mb-2">Vitalix</Text>
            <Text className="text-base text-[#526380]">Your personal health companion</Text>
          </View>

          {/* Form */}
          <View className="gap-4">
            <View>
              <Text className="text-sm text-[#526380] mb-1">Email</Text>
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
                autoComplete="email"
                placeholderTextColor="#526380"
                placeholder="you@example.com"
              />
            </View>

            <View>
              <Text className="text-sm text-[#526380] mb-1">Password</Text>
              <TextInput
                className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
                autoComplete="password"
                placeholderTextColor="#526380"
                placeholder="••••••••"
              />
            </View>

            {error && (
              <Text className="text-health-critical text-sm">{error}</Text>
            )}

            <TouchableOpacity
              onPress={handleLogin}
              disabled={loading}
              className="bg-primary-500 rounded-xl py-4 items-center mt-2"
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color="#080B10" />
              ) : (
                <Text className="text-obsidian-900 font-sansMedium text-base">Sign In</Text>
              )}
            </TouchableOpacity>
          </View>

          {/* OAuth divider */}
          <View className="flex-row items-center gap-3 mt-6">
            <View className="flex-1 h-px bg-surface-border" />
            <Text className="text-[#526380] text-xs">or</Text>
            <View className="flex-1 h-px bg-surface-border" />
          </View>

          {/* Apple / Google OAuth — requires native build (Phase 4) */}
          <View className="gap-3 mt-3">
            <TouchableOpacity
              disabled
              className="flex-row items-center justify-center gap-3 border border-surface-border rounded-xl py-3.5 opacity-40"
              activeOpacity={0.8}
            >
              <Ionicons name="logo-apple" size={20} color="#E8EDF5" />
              <Text className="text-[#E8EDF5] font-sansMedium">Continue with Apple</Text>
            </TouchableOpacity>
            <TouchableOpacity
              disabled
              className="flex-row items-center justify-center gap-3 border border-surface-border rounded-xl py-3.5 opacity-40"
              activeOpacity={0.8}
            >
              <Ionicons name="logo-google" size={18} color="#E8EDF5" />
              <Text className="text-[#E8EDF5] font-sansMedium">Continue with Google</Text>
            </TouchableOpacity>
            <Text className="text-[#3A4A5C] text-xs text-center">
              OAuth requires a native build (EAS). See MOBILE_ARCHITECTURE.md Section 8.
            </Text>
          </View>

          {/* Footer */}
          <View className="mt-6 items-center">
            <Text className="text-[#526380] text-sm">
              Don't have an account?{' '}
              <Link href="/(auth)/signup" className="text-primary-500">
                Sign up
              </Link>
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
