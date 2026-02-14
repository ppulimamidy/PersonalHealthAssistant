'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { useAuthStore } from '@/stores/authStore';
import type { UserProfile } from '@/types';

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const { user, setUser, setProfile, setLoading, isLoading } = useAuthStore();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();

        if (session?.user) {
          const md = (session.user.user_metadata ?? {}) as Record<string, unknown>;
          const profile: UserProfile = {
            age: typeof md.age === 'number' ? md.age : md.age ? Number(md.age) : undefined,
            gender: typeof md.gender === 'string' ? (md.gender as UserProfile['gender']) : undefined,
            weight_kg: typeof md.weight_kg === 'number' ? md.weight_kg : md.weight_kg ? Number(md.weight_kg) : undefined,
            profile_completed: Boolean(md.profile_completed),
          };

          setUser({
            id: session.user.id,
            email: session.user.email!,
            name: session.user.user_metadata?.name || 'User',
            created_at: session.user.created_at,
          });
          setProfile(profile);
        } else if (requireAuth) {
          router.push('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session?.user) {
          const md = (session.user.user_metadata ?? {}) as Record<string, unknown>;
          const profile: UserProfile = {
            age: typeof md.age === 'number' ? md.age : md.age ? Number(md.age) : undefined,
            gender: typeof md.gender === 'string' ? (md.gender as UserProfile['gender']) : undefined,
            weight_kg: typeof md.weight_kg === 'number' ? md.weight_kg : md.weight_kg ? Number(md.weight_kg) : undefined,
            profile_completed: Boolean(md.profile_completed),
          };

          setUser({
            id: session.user.id,
            email: session.user.email!,
            name: session.user.user_metadata?.name || 'User',
            created_at: session.user.created_at,
          });
          setProfile(profile);
        } else {
          setUser(null);
          setProfile(null);
          if (requireAuth) {
            router.push('/login');
          }
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [requireAuth, router, setUser, setLoading]);

  return { user, isLoading };
}
