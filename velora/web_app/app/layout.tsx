import type { Metadata } from 'next';
import './globals.css';
import { ToasterProvider } from '@/components/providers/toaster-provider';

export const metadata: Metadata = {
  title: 'VELORA TRADE TERMINAL',
  description: 'Institutional-grade trading terminal for disciplined traders.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
        <ToasterProvider />
      </body>
    </html>
  );
}
