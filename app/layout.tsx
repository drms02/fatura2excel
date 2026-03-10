import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Fatura2Excel — GİB E-Arşiv Faturalarını Excel\'e Dönüştür',
  description: 'GİB e-Arşiv PDF ve XML faturalarınızı saniyeler içinde düzenli Excel raporuna dönüştürün.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="tr">
        <body className={inter.className}>{children}</body>
      </html>
    </ClerkProvider>
  );
}
