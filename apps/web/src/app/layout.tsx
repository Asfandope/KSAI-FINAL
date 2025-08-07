import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "KS AI - Bilingual AI Assistant",
  description: "Get credible, contextual answers about Karthikeya Sivasenapathy's work in Politics, Environmentalism, SKCRF, and Educational Trust",
  keywords: ["KS", "AI Assistant", "Tamil", "English", "Politics", "Environment", "SKCRF"],
  authors: [{ name: "KS AI Team" }],
  openGraph: {
    title: "KS AI - Bilingual AI Assistant",
    description: "Get credible, contextual answers about Karthikeya Sivasenapathy",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-background">
          {children}
        </div>
      </body>
    </html>
  );
}