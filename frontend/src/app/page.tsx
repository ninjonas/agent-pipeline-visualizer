'use client';

import { useEffect, useState } from 'react';
import { fetchData } from './api/apiService';
import MultiAgentPanel from './components/MultiAgentPanel';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('Checking...');

  useEffect(() => {
    // Check API health
    fetchData<{ status: string; message: string }>('/health')
      .then((response) => {
        if (response.data) {
          setHealthStatus(`${response.data.status}: ${response.data.message}`);
        } else {
          setHealthStatus(`Error: ${response.error}`);
        }
      });
  }, []);

  return (
    <div className="grid grid-rows-[auto_1fr_auto] items-center justify-items-center min-h-screen p-4 sm:p-8 font-[family-name:var(--font-geist-sans)] text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900">
      <header className="w-full max-w-4xl py-4 mb-4">
        <h1 className="text-3xl font-bold text-center text-blue-600 dark:text-blue-400">AI Agent Pipeline Visualizer</h1>
      </header>
      <main className="flex flex-col gap-6 w-full max-w-4xl items-center">
        <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-md w-full border border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Backend Status</h2>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${healthStatus.includes('ok') ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <p className={`font-medium ${healthStatus.includes('ok') ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
              {healthStatus}
            </p>
          </div>
        </div>
        
        <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-slate-800 dark:to-slate-700 p-6 rounded-lg w-full border border-blue-100 dark:border-slate-600 text-center">
          <p className="text-gray-700 dark:text-gray-300">
            This application allows you to create, monitor, and interact with multiple AI agents. Each agent runs in its own folder.
          </p>
        </div>

        <MultiAgentPanel />
      </main>
      <footer className="w-full max-w-4xl py-6 mt-8 border-t border-gray-200 dark:border-gray-700">
        <p className="text-center text-gray-600 dark:text-gray-400">© {new Date().getFullYear()} AI Agent Pipeline Visualizer</p>
      </footer>
    </div>
  );
}
