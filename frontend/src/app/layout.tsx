import type { Metadata, Viewport } from "next";

import { Providers } from "@/components/providers";
import { themeBootstrapScript } from "@/lib/theme";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "AxiomQ", template: "%s · AxiomQ" },
  description: "Quantitative research infrastructure: backtesting, paper trading, experiments.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f6f8" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0d12" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootstrapScript }} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
