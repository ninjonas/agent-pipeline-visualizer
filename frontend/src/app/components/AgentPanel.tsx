'use client';

import { useState, useEffect } from 'react';
import { 
  getAgentTypes, 
  createAgent, 
  startAgent, 
  stopAgent, 
  getAgentStatus, 
  queryAgent,
  deleteAgent,
  AgentStatus,
  AgentConfig
} from '../api/agentService';

interface AgentPanelProps {
  agentId: string | null;
  isNew: boolean;
  onAgentCreated?: (agentId: string) => void;
  onAgentDeleted?: () => void;
}

export default function AgentPanel({
  agentId,
  isNew = false,
  onAgentCreated,
  onAgentDeleted
}: AgentPanelProps) {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>('');
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [agentTypes, setAgentTypes] = useState<string[]>([]);
  const [selectedAgentType, setSelectedAgentType] = useState<string>('openai');
  const [configJson, setConfigJson] = useState<string>('{}');
  const [isConfigValid, setIsConfigValid] = useState<boolean>(true);
  const [agentName, setAgentName] = useState<string>('');

  // Fetch agent status and available agent types on load
  useEffect(() => {
    fetchAgentTypes();
    
    if (agentId) {
      fetchAgentStatus();
      const interval = setInterval(fetchAgentStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [agentId]);

  const fetchAgentStatus = async () => {
    if (!agentId) return;
    
    const res = await getAgentStatus(agentId);
    if (res.data) {
      setStatus(res.data);
    }
  };

  const fetchAgentTypes = async () => {
    const res = await getAgentTypes();
    if (res.data?.agent_types) {
      setAgentTypes(res.data.agent_types);
      if (res.data.agent_types.length > 0 && !res.data.agent_types.includes(selectedAgentType)) {
        setSelectedAgentType(res.data.agent_types[0]);
      }
    }
  };

  const handleConfigChange = (value: string) => {
    setConfigJson(value);
    try {
      JSON.parse(value);
      setIsConfigValid(true);
    } catch (e) {
      setIsConfigValid(false);
    }
  };

  const handleCreateAgent = async () => {
    setLoading(true);
    setError(null);
    try {
      const config = isConfigValid ? JSON.parse(configJson) : {};
      const res = await createAgent(selectedAgentType, config, agentName || undefined);
      if (res.error) {
        setError(`Failed to create agent: ${res.error}`);
      } else if (res.data?.agent_id) {
        if (onAgentCreated) {
          onAgentCreated(res.data.agent_id);
        }
      }
    } catch (err) {
      setError('Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  const handleStartAgent = async () => {
    if (!agentId) return;
    
    setLoading(true);
    setError(null);
    try {
      const res = await startAgent(agentId);
      await fetchAgentStatus();
    } catch (err) {
      setError('Failed to start agent');
    } finally {
      setLoading(false);
    }
  };

  const handleStopAgent = async () => {
    if (!agentId) return;
    
    setLoading(true);
    setError(null);
    try {
      await stopAgent(agentId);
      await fetchAgentStatus();
    } catch (err) {
      setError('Failed to stop agent');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteAgent = async () => {
    if (!agentId) return;
    
    if (!window.confirm(`Are you sure you want to delete agent ${agentId}?`)) {
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      await deleteAgent(agentId);
      if (onAgentDeleted) {
        onAgentDeleted();
      }
    } catch (err) {
      setError('Failed to delete agent');
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !agentId) return;
    
    setLoading(true);
    setError(null);
    setResponse(null);
    
    try {
      const res = await queryAgent(agentId, prompt);
      if (res.data?.response) {
        setResponse(res.data.response);
      } else if (res.data?.error) {
        setError(res.data.error);
      } else if (res.error) {
        setError(res.error);
      }
    } catch (err) {
      setError('Failed to query agent');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white dark:bg-slate-800 rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">AI Agent</h2>
      
      {/* Agent Type Selection */}
      <div className="mb-4 p-4 border border-gray-200 rounded-lg">
        <h3 className="font-semibold mb-2">Agent Configuration</h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Agent Type
          </label>
          <select
            value={selectedAgentType}
            onChange={(e) => setSelectedAgentType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            disabled={loading || Boolean(status?.running)}
          >
            {agentTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Configuration (JSON)
          </label>
          <textarea
            value={configJson}
            onChange={(e) => handleConfigChange(e.target.value)}
            className={`w-full px-3 py-2 border ${
              isConfigValid ? 'border-gray-300' : 'border-red-500'
            } rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm`}
            rows={4}
            placeholder='{"key": "value"}'
            disabled={loading || Boolean(status?.running)}
          />
          {!isConfigValid && (
            <p className="mt-1 text-xs text-red-500">Invalid JSON format</p>
          )}
        </div>
        
        <button
          onClick={handleCreateAgent}
          disabled={loading || !isConfigValid || Boolean(status?.running)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
        >
          Create Agent
        </button>
      </div>

      {/* Agent Controls */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={handleStartAgent}
          disabled={loading || status?.running}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-400"
        >
          Start Agent
        </button>
        <button
          onClick={handleStopAgent}
          disabled={loading || !status?.running}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:bg-gray-400"
        >
          Stop Agent
        </button>
      </div>

      {/* Agent Status */}
      <div className="mb-4 p-4 border border-gray-200 rounded-lg">
        <h3 className="font-semibold mb-2">Status</h3>
        {status ? (
          <div>
            <p>
              <span className="font-medium">Status:</span>{" "}
              <span
                className={`px-2 py-1 rounded text-sm ${
                  status.running
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {status.status}
              </span>
            </p>
            {status.last_response && (
              <p className="mt-2">
                <span className="font-medium">Last Response:</span>{" "}
                <span className="text-gray-600">{status.last_response}</span>
              </p>
            )}
            {status.error && (
              <p className="mt-2">
                <span className="font-medium">Error:</span>{" "}
                <span className="text-red-600">{status.error}</span>
              </p>
            )}
          </div>
        ) : (
          <p className="text-gray-500">Loading status...</p>
        )}
      </div>

      {/* Agent Query Form */}
      <div className="mb-4">
        <h3 className="font-semibold mb-2">Query Agent</h3>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              rows={3}
              placeholder="Enter your message..."
              disabled={loading || !status?.running}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !status?.running || !prompt.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400"
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </form>
      </div>

      {/* Response Display */}
      {response && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h3 className="font-semibold mb-2">Response</h3>
          <div className="whitespace-pre-wrap">{response}</div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="font-semibold mb-2 text-red-700">Error</h3>
          <div className="text-red-600">{error}</div>
        </div>
      )}
    </div>
  );
}
