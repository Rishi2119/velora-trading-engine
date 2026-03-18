import { createClient } from '@/lib/supabase/client';

export async function fetchTrades() {
  const supabase = createClient();
  const { data, error } = await supabase
    .from('trades')
    .select('*')
    .order('opened_at', { ascending: false })
    .limit(20);

  if (error) throw error;
  return data;
}

export async function createJournalEntry(payload: {
  trade_id?: string | null;
  emotion: string;
  notes: string;
}) {
  const supabase = createClient();
  const { data, error } = await supabase.from('journals').insert(payload).select('*').single();

  if (error) throw error;
  return data;
}
