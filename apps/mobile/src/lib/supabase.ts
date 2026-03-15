import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL!;
const SUPABASE_KEY = process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY!;

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: {
    // AsyncStorage persists session across app restarts
    storage: AsyncStorage,
    // Supabase SDK auto-refreshes tokens before expiry
    autoRefreshToken: true,
    persistSession: true,
    // Required on React Native — no browser URL to parse auth params from
    detectSessionInUrl: false,
  },
});
