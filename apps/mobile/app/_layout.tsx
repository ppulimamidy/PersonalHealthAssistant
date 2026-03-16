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
import { api } from '@/services/api';

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
function AuthGate() {
  const { user, setUser } = useAuthStore();
  const [isInitialized, setIsInitialized] = useState(false);
  const segments = useSegments();
  const navigationState = useRootNavigationState();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setIsInitialized(true);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    // Wait for both: navigator mounted AND auth state confirmed
    if (!navigationState?.key || !isInitialized) return;

    const inAuthGroup = segments[0] === '(auth)';
    if (!user && !inAuthGroup) {
      router.replace('/(auth)/login');
    } else if (user && inAuthGroup) {
      router.replace('/(tabs)/home');
    }
  }, [user, segments, navigationState?.key, isInitialized]);

  return null;
}

function AppStateListener() {
  useEffect(() => {
    const subscription = AppState.addEventListener(
      'change',
      (nextState: AppStateStatus) => {
        if (nextState === 'active') {
          queryClient.invalidateQueries({ queryKey: ['batch'] });
          queryClient.invalidateQueries({ queryKey: ['oura-connection'] });
        }
      }
    );
    return () => subscription.remove();
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
        <StatusBar style="light" />
        {/* Slot FIRST — mounts the navigator before AuthGate fires its effects */}
        <Slot />
        <AuthGate />
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
