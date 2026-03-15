import type { Metadata, Viewport } from 'next';
import { Syne, DM_Sans, DM_Mono } from 'next/font/google';
import '@/styles/globals.css';
import { Providers } from './providers';
import { Toaster } from '@/components/ui/toaster';
import { ServiceWorkerRegistration } from '@/components/ServiceWorkerRegistration';

const syne = Syne({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-syne',
  display: 'swap',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600'],
  style: ['normal', 'italic'],
  variable: '--font-dm-sans',
  display: 'swap',
});

const dmMono = DM_Mono({
  subsets: ['latin'],
  weight: ['300', '400', '500'],
  variable: '--font-dm-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Personal Health Assistant',
  description: 'Your AI-powered personal health companion',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'HealthAI',
  },
};

export const viewport: Viewport = {
  themeColor: '#00D4AA',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${syne.variable} ${dmSans.variable} ${dmMono.variable}`}>
      <body className={dmSans.className}>
        <ServiceWorkerRegistration />
        <Providers>{children}</Providers>
        <Toaster />
      </body>
    </html>
  );
}
