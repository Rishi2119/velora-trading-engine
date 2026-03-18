const TESTIMONIALS = [
  {
    name: 'R. Khanna',
    role: 'Prop Trader',
    quote: 'Velora made me aware of my emotional leakage. My drawdowns dropped in 6 weeks.',
  },
  {
    name: 'J. Mercer',
    role: 'FX Swing Trader',
    quote: 'The discipline score and streak mechanics changed how I approach every setup.',
  },
];

export function TestimonialsSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-12">
      <h2 className="font-display text-3xl">Trader stories</h2>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {TESTIMONIALS.map((testimonial) => (
          <article key={testimonial.name} className="velora-card p-5">
            <p className="text-slate-200">\"{testimonial.quote}\"</p>
            <p className="mt-4 text-sm text-slate-400">
              {testimonial.name} · {testimonial.role}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
