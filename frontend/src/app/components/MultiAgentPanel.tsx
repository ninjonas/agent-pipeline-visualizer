'use client';

import { useState, useEffect } from 'react';
import { getAgents, AgentInfo } from '../api/agentService';
import AgentPanel from './AgentPanel';

export default function MultiAgentPanel() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [showNewAgentForm, setShowNewAgentForm] = useState<boolean>(false);

  // Load agents on component mount
  useEffect(() => {
    fetchAgents();
    
    // Auto-refresh agents list every 10 seconds
    const interval = setInterval(fetchAgents, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch the list of agents from the backend
  const fetchAgents = async () => {
    try {
      const response = await getAgents();
      if (response.data?.agents) {
        setAgents(response.data.agents);
        
        // If no agent is selected yet and we have agents, select the first one
        if (!selectedAgentId && response.data.agents.length > 0) {
          setSelectedAgentId(response.data.agents[0].agent_id);
        }
      } else if (response.error) {
        setError(response.error);
      }
    } catch (err) {
      setError('Failed to fetch agents');
    } finally {
      setLoading(false);
    }
  };

  // Handle agent creation
  const handleAgentCreated = (agentId: string) => {
    setSelectedAgentId(agentId);
    setShowNewAgentForm(false);
    fetchAgents();
  };

  // Handle agent deletion
  const handleAgentDeleted = () => {
    setSelectedAgentId(null);
    fetchAgents();
  };

  return (
    <div className="w-full">
      {/* Agents Navigation */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <h2 className="text-xl font-bold text-gray-800 dark:text-white">Agents</h2>
        
        <div className="flex-grow overflow-x-auto">
          <div className="flex gap-2">
            {agents.map(agent => (
              <button
                key={agent.agent_id}
                onClick={() => {
                  setSelectedAgentId(agent.agent_id);
                  setShowNewAgentForm(false);
                }}
                className={`px-4 py-2 rounded-md text-sm whitespace-nowrap ${
                  selectedAgentId === agent.agent_id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                {agent.name}
                <span className={`ml-2 w-2 h-2 inline-block rounded-full ${
                  agent.running ? 'bg-green-500' : 'bg-red-500'
                }`}></span>
              </button>
            ))}
          </div>
        </div>
        
        <button
          onClick={() => {
            setShowNewAgentForm(true);
            setSelectedAgentId(null);
          }}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Create New Agent
        </button>
      </div>

      {/* Loading State */}
      {loading && !showNewAgentForm && !selectedAgentId && (
        <div className="p-4 bg-white dark:bg-slate-800 rounded-lg shadow text-center">
          <p className="text-gray-600 dark:text-gray-300">Loading agents...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-lg">
          <h3 className="font-semibold mb-2 text-red-700 dark:text-red-300">Error</h3>
          <div className="text-red-600 dark:text-red-200">{error}</div>
        </div>
      )}

      {/* No Agents State */}
      {!loading && agents.length === 0 && !showNewAgentForm && (
        <div className="p-4 bg-white dark:bg-slate-800 rounded-lg shadow text-center">
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            No agents available. Create your first agent to get started.
          </p>
          <button
            onClick={() => setShowNewAgentForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Create Agent
          </button>
        </div>
      )}

      {/* New Agent Form */}
      {showNewAgentForm && (
        <AgentPanel
          agentId={null}
          isNew={true}
          onAgentCreated={handleAgentCreated}
        />
      )}

      {/* Selected Agent Interface */}
      {selectedAgentId && (
        <AgentPanel
          agentId={selectedAgentId}
          isNew={false}
          onAgentDeleted={handleAgentDeleted}
        />
      )}
    </div>
  );
}