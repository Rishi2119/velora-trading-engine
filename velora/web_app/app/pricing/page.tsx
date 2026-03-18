const PLANS = [
  {
    name: 'Free',
    price: '$0/mo',
    features: ['Portfolio snapshot', 'Basic journaling', 'Standard support'],
  },
  {
    name: 'Pro',
    price: '$29/mo',
    features: ['Advanced analytics', 'Full journal insights', 'Discipline tracking'],
  },
  {
    name: 'Premium',
    price: '$99/mo',
    features: ['AI coaching', 'Priority support', 'Elite performance reports'],
  },
];

export default function PricingPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="font-display text-4xl">Pricing</h1>
      <p className="mt-2 text-slate-300">Choose the plan that matches your trading ambition.</p>
      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {PLANS.map((plan) => (
          <article key={plan.name} className="velora-card p-6">
            <h2 className="font-display text-2xl">{plan.name}</h2>
            <p className="mt-2 text-3xl text-electric">{plan.price}</p>
            <ul className="mt-4 space-y-2 text-sm text-slate-300">
              {plan.features.map((feature) => (
                <li key={feature}>- {feature}</li>
              ))}
            </ul>
            <button className="mt-6 w-full rounded-xl bg-premium px-4 py-3 font-semibold text-black">Choose {plan.name}</button>
          </article>
        ))}
      </div>
    </main>
  );
}
