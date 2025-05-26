import Link from 'next/link';

export default function Home() {
  return (
    <div className="container mx-auto py-12">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 text-primary-700">Agent Pipeline Visualizer</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          A framework for visualizing AI agent actions and steps when processing data.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        <Link href="/agent" className="group">
          <div className="border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-all h-full bg-white">
            <h2 className="text-2xl font-semibold mb-3 text-primary-600 group-hover:text-primary-700">
              Agent Dashboard
            </h2>
            <p className="text-gray-600">
              View the current status of agent steps and interact with generated outputs.
            </p>
          </div>
        </Link>

        <Link href="/configuration" className="group">
          <div className="border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-all h-full bg-white">
            <h2 className="text-2xl font-semibold mb-3 text-primary-600 group-hover:text-primary-700">
              Agent Configuration
            </h2>
            <p className="text-gray-600">
              Configure agent steps and their dependencies for your specific use case.
            </p>
          </div>
        </Link>
      </div>
      
      <div className="mt-16 text-center">
        <h2 className="text-2xl font-semibold mb-4 text-gray-800">Getting Started</h2>
        <div className="bg-white p-6 rounded-lg shadow-sm max-w-3xl mx-auto">
          <ol className="text-left list-decimal pl-6 space-y-2">
            <li>View the agent dashboard to monitor step status</li>
            <li>Start the agent using <code className="bg-gray-100 px-2 py-1 rounded">./run.sh agent-run step</code></li>
            <li>Wait for the agent run to complete and files to be generated</li>
            <li>Review and approve generated files in each step</li>
            <li>Configure steps and dependencies as needed</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
