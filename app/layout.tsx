import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Fatura2Excel — E-Arşiv Fatura Excel\'e Dönüştür | GİB PDF & XML',
  description: 'GİB e-Arşiv PDF ve XML faturalarınızı saniyeler içinde düzenli Excel raporuna dönüştürün. İlk 5 fatura ücretsiz. Muhasebeciler için toplu fatura dönüştürme aracı.',
  keywords: [
    'e-arşiv excel dönüştür',
    'e-arşiv fatura excel',
    'gib fatura excel',
    'pdf fatura excel',
    'xml fatura excel',
    'e-fatura excel dönüştürme',
    'e-arşiv pdf dönüştürme',
    'fatura excel muhasebe',
    'toplu fatura dönüştürme',
    'gib e-arşiv pdf excel',
  ],
  openGraph: {
    title: 'Fatura2Excel — E-Arşiv Faturalarını Anında Excel\'e Dönüştür',
    description: 'GİB e-Arşiv PDF ve XML faturalarınızı saniyeler içinde Excel\'e dönüştürün. İlk 5 fatura ücretsiz!',
    type: 'website',
    locale: 'tr_TR',
  },
  robots: {
    index: true,
    follow: true,
  },
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
