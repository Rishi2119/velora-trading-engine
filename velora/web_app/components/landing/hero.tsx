import Link from 'next/link';

export function HeroSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-12 md:pt-20">
      <div className="grid gap-10 md:grid-cols-2 md:items-center">
        <div>
          <p className="mb-3 inline-flex rounded-full border border-electric/30 px-3 py-1 text-xs uppercase tracking-[0.2em] text-electric">
            Premium Trader OS
          </p>
          <h1 className="font-display text-4xl leading-tight md:text-6xl">
            Trade with precision.
            <span className="block text-profit">Win with discipline.</span>
          </h1>
          <p className="mt-5 max-w-xl text-base text-slate-300 md:text-lg">
            VELORA blends institutional execution dashboards with performance psychology so you can compound consistency, not chaos.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/auth/login" className="rounded-xl bg-electric px-6 py-3 font-semibold text-white shadow-glow">
              Start Free
            </Link>
            <Link href="/pricing" className="rounded-xl border border-white/20 px-6 py-3 font-semibold text-white">
              View Pricing
            </Link>
          </div>
        </div>
        <div className="velora-card p-6">
          <p className="text-sm text-slate-300">Session Performance</p>
          <p className="mt-3 font-display text-3xl text-profit">+4.21%</p>
          <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-xl bg-white/5 p-3">
              <p className="text-slate-400">Daily Streak</p>
              <p className="mt-1 text-xl font-semibold text-premium">14 Days</p>
            </div>
            <div className="rounded-xl bg-white/5 p-3">
              <p className="text-slate-400">Discipline Score</p>
              <p className="mt-1 text-xl font-semibold text-profit">89/100</p>
            </div>
          </div>
          <p className="mt-5 text-sm text-slate-300">\"Discipline beats emotion. Process beats prediction.\"</p>
        </div>
      </div>
    </section>
  );
}
