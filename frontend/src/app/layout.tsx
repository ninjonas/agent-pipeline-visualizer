import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Agent Pipeline Visualizer",
  description: "A web application for visualizing multi-step agent pipelines",
};

function Navigation() {
  return (
    <nav className="bg-blue-600 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-xl font-bold">
          Agent Pipeline Visualizer
        </Link>
        <div className="space-x-6">
          <Link href="/" className="hover:text-blue-200 transition">
            Home
          </Link>
          <Link href="/agent" className="hover:text-blue-200 transition">
            Agent Dashboard
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-slate-100`}
      >
        <Navigation />
        <main>{children}</main>
      </body>
    </html>
  );
}
