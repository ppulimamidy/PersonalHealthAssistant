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
import * as Haptics from 'expo-haptics';
import { supabase } from '@/lib/supabase';

export default function SignupScreen() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSignup() {
    if (!name || !email || !password) {
      setError('All fields are required');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { error: authError } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: { data: { full_name: name.trim() } },
      });
      if (authError) throw authError;
      // Profile row auto-created by database trigger on auth.users INSERT

      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.replace('/(auth)/onboarding');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Signup failed';
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
      <ScrollView contentContainerStyle={{ flexGrow: 1 }} keyboardShouldPersistTaps="handled">
        <View className="flex-1 justify-center px-6 py-12">
          <View className="mb-10">
            <Text className="text-3xl font-display text-[#E8EDF5] mb-2">Create account</Text>
            <Text className="text-base text-[#526380]">Start your health journey</Text>
          </View>

          <View className="gap-4">
            {(['Name', 'Email', 'Password'] as const).map((label) => (
              <View key={label}>
                <Text className="text-sm text-[#526380] mb-1">{label}</Text>
                <TextInput
                  className="bg-surface-raised border border-surface-border rounded-xl px-4 py-3 text-[#E8EDF5] text-base"
                  value={label === 'Name' ? name : label === 'Email' ? email : password}
                  onChangeText={label === 'Name' ? setName : label === 'Email' ? setEmail : setPassword}
                  autoCapitalize={label === 'Name' ? 'words' : 'none'}
                  keyboardType={label === 'Email' ? 'email-address' : 'default'}
                  secureTextEntry={label === 'Password'}
                  placeholderTextColor="#526380"
                  placeholder={label === 'Email' ? 'you@example.com' : label === 'Password' ? '8+ characters' : 'Your name'}
                />
              </View>
            ))}

            {error && <Text className="text-health-critical text-sm">{error}</Text>}

            <TouchableOpacity
              onPress={handleSignup}
              disabled={loading}
              className="bg-primary-500 rounded-xl py-4 items-center mt-2"
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color="#080B10" />
              ) : (
                <Text className="text-obsidian-900 font-sansMedium text-base">Create Account</Text>
              )}
            </TouchableOpacity>
          </View>

          <View className="mt-8 items-center">
            <Text className="text-[#526380] text-sm">
              Already have an account?{' '}
              <Link href="/(auth)/login" className="text-primary-500">Sign in</Link>
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
