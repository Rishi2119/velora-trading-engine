import { createClient } from '@/lib/supabase/client';
import type { SubscriptionPlan } from '@/lib/types';

export async function fetchSubscription() {
  const supabase = createClient();
  const { data, error } = await supabase
    .from('subscriptions')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  return data;
}

export async function changePlan(plan: SubscriptionPlan) {
  const supabase = createClient();
  const { data, error } = await supabase.rpc('upsert_subscription_plan', { p_plan: plan });

  if (error) throw error;
  return data;
}
