import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import type { SupabaseClient } from "@supabase/supabase-js";

/**
 * Browser/client-side Supabase client.
 *
 * Uses `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` from the
 * environment (configure in Vercel → Project → Settings → Environment Variables).
 */
export function createSupabaseClient(): SupabaseClient {
  return createClientComponentClient();
}

export const supabase = createSupabaseClient();
