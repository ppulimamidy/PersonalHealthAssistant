'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { useAuthStore } from '@/stores/authStore';
import { useSubscriptionStore } from '@/stores/subscriptionStore';
import { billingService } from '@/services/billing';
import type { UserProfile } from '@/types';

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const { user, setUser, setProfile, setLoading, isLoading } = useAuthStore();
  const setSubscription = useSubscriptionStore((s) => s.setSubscription);

  useEffect(() => {
    const buildProfile = async (userId: string): Promise<UserProfile> => {
      const { data: row } = await supabase
        .from('profiles')
        .select('date_of_birth,biological_sex,weight_kg,primary_goals,onboarding_completed_at')
        .eq('id', userId)
        .single();
      return {
        date_of_birth: row?.date_of_birth ?? undefined,
        biological_sex: row?.biological_sex ?? undefined,
        weight_kg: row?.weight_kg ?? undefined,
        primary_goals: Array.isArray(row?.primary_goals) ? row.primary_goals : undefined,
        onboarding_completed_at: row?.onboarding_completed_at ?? undefined,
        profile_completed: Boolean(row?.onboarding_completed_at),
      };
    };

    const checkAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();

        if (session?.user) {
          setUser({
            id: session.user.id,
            email: session.user.email!,
            name: session.user.user_metadata?.name || 'User',
            created_at: session.user.created_at,
          });

          // Non-blocking: profile and subscription hydrate after auth check
          buildProfile(session.user.id).then(setProfile).catch(() => {});
          billingService.getSubscription().then(setSubscription).catch(() => {});
        } else if (requireAuth) {
          router.push('/login');
        }
      } finally {
        // Unblock the layout immediately after session check — don't wait for profile fetch
        setLoading(false);
      }
    };

    checkAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (session?.user) {
          setUser({
            id: session.user.id,
            email: session.user.email!,
            name: session.user.user_metadata?.name || 'User',
            created_at: session.user.created_at,
          });
          buildProfile(session.user.id).then(setProfile).catch(() => {});
          billingService.getSubscription().then(setSubscription).catch(() => {});
        } else {
          setUser(null);
          setProfile(null);
          setSubscription(null);
          if (requireAuth) {
            router.push('/login');
          }
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [requireAuth, router, setUser, setLoading, setSubscription]);

  return { user, isLoading };
}
