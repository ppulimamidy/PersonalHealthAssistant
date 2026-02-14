import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * Browser/client-side Supabase client.
 *
 * Supabase has migrated away from legacy JWT-based `anon` keys in many projects.
 * Prefer using the new Publishable key:
 *
 * - `NEXT_PUBLIC_SUPABASE_URL`
 * - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (preferred)
 *
 * For backward compatibility we still accept:
 * - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
 */
export function createSupabaseClient(): SupabaseClient {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseKey) {
    throw new Error(
      "Missing Supabase env vars. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (preferred)."
    );
  }

  return createClientComponentClient({
    supabaseUrl,
    supabaseKey,
  });
}

export const supabase = createSupabaseClient();
