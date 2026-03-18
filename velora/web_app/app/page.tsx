import { FeaturesSection } from '@/components/landing/features';
import { HeroSection } from '@/components/landing/hero';
import { PricingPreviewSection } from '@/components/landing/pricing-preview';
import { TestimonialsSection } from '@/components/landing/testimonials';

export default function LandingPage() {
  return (
    <main>
      <HeroSection />
      <FeaturesSection />
      <TestimonialsSection />
      <PricingPreviewSection />
      <footer className="mx-auto max-w-6xl px-6 py-10 text-sm text-slate-400">
        2026 VELORA TRADE TERMINAL. Built for disciplined execution.
      </footer>
    </main>
  );
}
