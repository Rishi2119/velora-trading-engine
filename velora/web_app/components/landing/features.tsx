const FEATURES = [
  {
    title: 'Execution Intelligence',
    description: 'Live positions, PnL breakdown, and risk overlays with institutional clarity.',
  },
  {
    title: 'Behavioral Analytics',
    description: 'Track emotional drift, overtrading frequency, and discipline consistency by session.',
  },
  {
    title: 'Plan-Based Power',
    description: 'Unlock advanced journals, AI insights, and premium playbooks as you scale.',
  },
];

export function FeaturesSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-12">
      <h2 className="font-display text-3xl">Built for serious traders</h2>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {FEATURES.map((feature) => (
          <article key={feature.title} className="velora-card p-5">
            <h3 className="font-display text-xl">{feature.title}</h3>
            <p className="mt-2 text-sm text-slate-300">{feature.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
