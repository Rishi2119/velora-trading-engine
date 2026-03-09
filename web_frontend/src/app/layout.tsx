import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Velora — AI Trading Platform",
  description: "Institutional-grade AI-powered forex & crypto trading dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
