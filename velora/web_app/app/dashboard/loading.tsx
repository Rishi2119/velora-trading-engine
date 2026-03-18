export default function DashboardLoading() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-2xl bg-white/10" />
        ))}
      </div>
      <div className="mt-8 h-64 animate-pulse rounded-2xl bg-white/10" />
    </main>
  );
}
