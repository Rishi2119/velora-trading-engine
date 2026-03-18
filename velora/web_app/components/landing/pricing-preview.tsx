import Link from 'next/link';

const PLANS = [
  { name: 'Free', price: '$0', points: ['Basic dashboard', 'Limited journals'] },
  { name: 'Pro', price: '$29', points: ['Advanced analytics', 'Unlimited journals'] },
  { name: 'Premium', price: '$99', points: ['AI insights', 'Performance coaching'] },
];

export function PricingPreviewSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-12">
      <h2 className="font-display text-3xl">Plans that scale with your edge</h2>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {PLANS.map((plan) => (
          <article key={plan.name} className="velora-card p-5">
            <h3 className="font-display text-2xl">{plan.name}</h3>
            <p className="mt-2 text-3xl font-bold text-electric">{plan.price}<span className="text-sm text-slate-400">/mo</span></p>
            <ul className="mt-4 space-y-2 text-sm text-slate-300">
              {plan.points.map((point) => (
                <li key={point}>- {point}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
      <Link href="/pricing" className="mt-6 inline-block rounded-xl bg-premium px-5 py-3 font-semibold text-black">
        Compare Full Plans
      </Link>
    </section>
  );
}
