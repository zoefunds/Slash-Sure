import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import { Providers } from "@/components/layout/Providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SlashSure — AI-Powered Trust & Insurance for Decentralized Networks",
  description:
    "The AI-native slashing monitoring, risk assessment, and insurance coordination layer for validators, AVSs, oracle networks, and restaking ecosystems. Powered by GenLayer.",
  keywords: [
    "slashing", "validator insurance", "EigenLayer", "restaking", "AVS",
    "oracle network", "DePIN", "GenLayer", "blockchain security", "validator monitoring",
  ],
  openGraph: {
    title: "SlashSure",
    description: "AI-powered trust, slashing, and insurance layer for decentralized networks",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-background antialiased" style={{ fontFamily: "var(--font-inter), system-ui, sans-serif" }}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
