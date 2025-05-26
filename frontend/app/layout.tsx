import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Agent Pipeline Visualizer',
  description: 'Visualize AI agent actions and steps',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="bg-white shadow-sm">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <Link href="/" className="text-xl font-bold text-primary-700">
                Agent Pipeline Visualizer
              </Link>
              <nav>
                <ul className="flex space-x-6">
                  <li>
                    <Link href="/" className="text-gray-600 hover:text-primary-600">
                      Home
                    </Link>
                  </li>
                  <li>
                    <Link href="/agent" className="text-gray-600 hover:text-primary-600">
                      Agent Dashboard
                    </Link>
                  </li>
                  <li>
                    <Link href="/configuration" className="text-gray-600 hover:text-primary-600">
                      Configuration
                    </Link>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </header>
        <main className="min-h-screen">
          {children}
        </main>
        <footer className="bg-gray-50 py-6 mt-12">
          <div className="container mx-auto px-4">
            <p className="text-center text-gray-500 text-sm">
              &copy; {new Date().getFullYear()} Agent Pipeline Visualizer. All rights reserved.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
