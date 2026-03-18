import { createClient } from '@/lib/supabase/server';

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: profile } = await supabase.from('profiles').select('*').maybeSingle();
  const { data: trades } = await supabase
    .from('trades')
    .select('symbol, side, pnl, opened_at')
    .order('opened_at', { ascending: false })
    .limit(8);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="grid gap-4 md:grid-cols-4">
        <article className="velora-card p-4">
          <p className="text-sm text-slate-400">Daily Streak</p>
          <p className="mt-2 font-display text-3xl text-premium">{profile?.daily_streak ?? 0}</p>
        </article>
        <article className="velora-card p-4">
          <p className="text-sm text-slate-400">Discipline Score</p>
          <p className="mt-2 font-display text-3xl text-profit">{profile?.discipline_score ?? 0}</p>
        </article>
        <article className="velora-card p-4 md:col-span-2">
          <p className="text-sm text-slate-400">Motivational Quote</p>
          <p className="mt-2 text-lg">{profile?.quote_of_day ?? 'Discipline beats emotion.'}</p>
        </article>
      </div>

      <section className="mt-8 velora-card p-6">
        <h2 className="font-display text-2xl">Recent Trades</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="pb-2">Symbol</th>
                <th className="pb-2">Side</th>
                <th className="pb-2">PnL</th>
                <th className="pb-2">Opened</th>
              </tr>
            </thead>
            <tbody>
              {(trades ?? []).map((trade) => (
                <tr key={`${trade.symbol}-${trade.opened_at}`} className="border-t border-white/10">
                  <td className="py-2">{trade.symbol}</td>
                  <td className="py-2 uppercase">{trade.side}</td>
                  <td className={`py-2 ${(trade.pnl ?? 0) >= 0 ? 'text-profit' : 'text-loss'}`}>
                    {trade.pnl ?? 0}
                  </td>
                  <td className="py-2 text-slate-400">{new Date(trade.opened_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
