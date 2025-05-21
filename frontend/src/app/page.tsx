"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import Link from "next/link";

interface StatusResponse {
  status: string;
  message: string;
}

export default function Home() {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [steps, setSteps] = useState<string[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("http://localhost:4000/api/status");

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    const fetchSteps = async () => {
      try {
        const response = await fetch("http://localhost:4000/api/steps");
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const result = await response.json();
        setSteps(result.steps);
      } catch (err) {
        console.error("Failed to fetch steps:", err);
      }
    };

    fetchData();
    fetchSteps();
  }, []);

  return (
    <div className="min-h-screen p-8">
      <main className="container mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-gray-900">
            Agent Pipeline Visualizer
          </h1>
          <p className="text-xl text-gray-700 max-w-3xl mx-auto">
            A tool for visualizing and managing multi-step agent workflows
          </p>
        </div>

        {/* Backend Status */}
        <div className="w-full max-w-md mx-auto p-4 bg-white shadow-md rounded-lg border mb-10">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">
            Backend Connection
          </h2>

          {loading ? (
            <p className="text-blue-600">Loading backend status...</p>
          ) : error ? (
            <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
              <p>Error connecting to backend: {error}</p>
              <p className="text-sm mt-2">
                Make sure the Flask API is running on port 4000
              </p>
            </div>
          ) : (
            <div className="p-4 bg-green-100 border border-green-400 text-green-700 rounded">
              <p>
                <strong>Status:</strong> {data?.status}
              </p>
              <p>
                <strong>Message:</strong> {data?.message}
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          <div className="bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Agent Dashboard
            </h2>
            <p className="text-gray-700 mb-6">
              Monitor the status of agent pipelines, track progress of steps,
              and visualize results.
            </p>
            <div>
              <Link
                href="/agent"
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 inline-block"
              >
                Go to Dashboard
              </Link>
            </div>
          </div>

          <div className="bg-white p-8 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold mb-4 text-gray-900">
              Integration Guide
            </h2>
            <p className="text-gray-700 mb-6">
              Learn how to integrate your own agents with the pipeline
              visualizer.
            </p>
            <div className="text-sm bg-gray-800 text-white p-4 rounded-md">
              <h3 className="font-medium mb-2">Quick Setup</h3>
              <code className="block mb-4 text-green-300">
                cd agent
                <br />
                python -m venv venv
                <br />
                source venv/bin/activate
                <br />
                pip install -r requirements.txt
              </code>
              <h3 className="font-medium mb-2">Run Demo Agent</h3>
              <code className="block text-green-300">
                ./run.sh agent-run step
              </code>
            </div>
          </div>
        </div>

        <div className="mt-12 max-w-5xl mx-auto">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900">
            How It Works
          </h2>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <ol className="list-decimal pl-5 space-y-4 text-gray-800">
              <li>
                <strong className="text-gray-900">Register a pipeline</strong> -
                Initialize a new processing pipeline and get a unique ID
              </li>
              <li>
                <strong className="text-gray-900">Execute steps</strong> - Run
                individual steps in your processing pipeline
              </li>
              <li>
                <strong className="text-gray-900">Monitor progress</strong> -
                Track the status and results of each step
              </li>
              <li>
                <strong className="text-gray-900">Visualize results</strong> -
                See the output data from each completed step
              </li>
            </ol>

            <div className="mt-6 border-t border-gray-200 pt-4">
              <p className="text-gray-800">
                Check out the{" "}
                <code className="bg-gray-800 text-green-300 px-2 py-1 rounded">
                  agent
                </code>{" "}
                directory for sample code that demonstrates how to integrate
                your own agents with this visualization tool.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-12 max-w-5xl mx-auto">
          <h2 className="text-2xl font-semibold mb-4 text-gray-900">
            Steps to Execute
          </h2>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <ol className="list-decimal pl-5 space-y-4 text-gray-800">
              {steps.length > 0 ? (
                steps.map((step, index) => (
                  <li key={index}>
                    <strong className="text-gray-900">{step}</strong>
                  </li>
                ))
              ) : (
                <p className="text-gray-700">No steps available.</p>
              )}
            </ol>
          </div>
        </div>
      </main>
    </div>
  );
}
