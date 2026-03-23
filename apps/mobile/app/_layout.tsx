import '../global.css';
import { useEffect, useState } from 'react';
import { AppState, AppStateStatus, Linking } from 'react-native';
import { Slot, router, useSegments, useRootNavigationState } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import { Syne_700Bold } from '@expo-google-fonts/syne';
import { DMSans_400Regular, DMSans_500Medium } from '@expo-google-fonts/dm-sans';
import * as SplashScreen from 'expo-splash-screen';
import { supabase } from '@/lib/supabase';
import { useAuthStore } from '@/stores/authStore';
import { api, refreshTokenCache, forceLogout } from '@/services/api';
import { setupNotificationListeners } from '@/services/notifications';

// Keep splash visible until fonts are ready
SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

// Auth gate — waits for both auth state and navigator to be ready
async function fetchProfile(userId: string) {
  try {
    const { data: row } = await supabase
      .from('profiles')
      .select('date_of_birth,biological_sex,weight_kg,height_cm,primary_goals,onboarding_completed_at,last_checkin_at,user_role')
      .eq('id', userId)
      .single();
    if (row) {
      return {
        date_of_birth: row.date_of_birth ?? undefined,
        biological_sex: row.biological_sex ?? undefined,
        weight_kg: row.weight_kg ?? undefined,
        height_cm: row.height_cm ?? undefined,
        primary_goals: Array.isArray(row.primary_goals) ? row.primary_goals : undefined,
        onboarding_completed_at: row.onboarding_completed_at ?? undefined,
        last_checkin_at: row.last_checkin_at ?? undefined,
        user_role: row.user_role ?? 'patient',
      };
    }
  } catch (e) {
    console.warn('Failed to fetch profile:', e);
  }
  return null;
}

function AuthGate() {
  const { user, setUser, setProfile } = useAuthStore();
  const [isInitialized, setIsInitialized] = useState(false);
  const segments = useSegments();
  const navigationState = useRootNavigationState();

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      const sessionUser = session?.user ?? null;
      setUser(sessionUser);
      if (sessionUser) {
        const profile = await fetchProfile(sessionUser.id);
        setProfile(profile);
      }
      setIsInitialized(true);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        const sessionUser = session?.user ?? null;
        setUser(sessionUser);
        if (sessionUser) {
          const profile = await fetchProfile(sessionUser.id);
          setProfile(profile);
        } else {
          setProfile(null);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    // Wait for both: navigator mounted AND auth state confirmed
    if (!navigationState?.key || !isInitialized) return;

    const inAuthGroup = segments[0] === '(auth)';
    const inOnboarding = segments[1] === 'onboarding';
    if (!user && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (user && inAuthGroup && !inOnboarding) {
      // Allow onboarding to stay in auth group — only redirect login/signup
      router.replace('/(tabs)/home');
    }
  }, [user, segments, navigationState?.key, isInitialized]);

  return null;
}

function AppStateListener() {
  useEffect(() => {
    const subscription = AppState.addEventListener(
      'change',
      async (nextState: AppStateStatus) => {
        if (nextState === 'active') {
          // Refresh token cache and verify session is still valid
          try {
            const isValid = await refreshTokenCache();
            if (!isValid) {
              // Session truly expired — force logout
              useAuthStore.getState().logout();
              forceLogout();
              return;
            }
          } catch {
            // Network error during refresh — let queries handle 401
          }
          // Invalidate all data queries so screens show fresh data
          queryClient.invalidateQueries();
        }
      }
    );
    return () => subscription.remove();
  }, []);
  return null;
}

function NotificationListener() {
  useEffect(() => {
    const cleanup = setupNotificationListeners((screen) => {
      // Navigate based on the screen hint from the nudge data
      if (screen === 'home') {
        router.push('/(tabs)/home');
      } else if (screen === 'insights') {
        router.push('/(tabs)/insights');
      } else if (screen === 'profile') {
        router.push('/(tabs)/profile');
      } else {
        router.push('/(tabs)/home');
      }
      // Refresh home data after navigating
      queryClient.invalidateQueries({ queryKey: ['active-intervention'] });
      queryClient.invalidateQueries({ queryKey: ['latest-result'] });
      queryClient.invalidateQueries({ queryKey: ['top-recommendation'] });
    });
    return cleanup;
  }, []);
  return null;
}

function DeepLinkHandler() {
  useEffect(() => {
    const handleUrl = async (url: string) => {
      if (url.startsWith('vitalix://oura-callback')) {
        try {
          const parsed = new URL(url);
          const code = parsed.searchParams.get('code');
          if (code) {
            await api.post('/api/v1/oura/callback', { code });
            queryClient.invalidateQueries({ queryKey: ['oura-connection'] });
          }
        } catch (_e) {
          // silent — user will see disconnected state
        }
      }
    };

    const subscription = Linking.addEventListener('url', ({ url }) => handleUrl(url));
    Linking.getInitialURL().then((url) => { if (url) handleUrl(url); });
    return () => subscription.remove();
  }, []);
  return null;
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Syne_700Bold,
    DMSans_400Regular,
    DMSans_500Medium,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  // Don't render until fonts are ready (prevents ???? flash)
  if (!fontsLoaded && !fontError) return null;

  return (
    <GestureHandlerRootView className="flex-1 bg-obsidian-900">
      <QueryClientProvider client={queryClient}>
        <AppStateListener />
        <DeepLinkHandler />
        <NotificationListener />
        <StatusBar style="light" />
        {/* Slot FIRST — mounts the navigator before AuthGate fires its effects */}
        <Slot />
        <AuthGate />
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
