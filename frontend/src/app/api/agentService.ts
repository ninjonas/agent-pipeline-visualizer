import { fetchData, postData, deleteData, ApiResponse } from './apiService';

export interface AgentStatus {
  status: string;
  running: boolean;
  last_response: string | null;
  error: string | null;
  conversation_length?: number;
  model?: string;
}

export interface AgentResponse {
  response?: string;
  error?: string;
}

export interface AgentConfig {
  [key: string]: any;
}

export interface AgentInfo {
  agent_id: string;
  name: string;
  agent_type: string;
  status: string;
  running: boolean;
}

/**
 * Get a list of all available agents
 */
export async function getAgents(): Promise<ApiResponse<{agents: AgentInfo[]}>> {
  return await fetchData<{agents: AgentInfo[]}>('/agents');
}

/**
 * Get available agent types from the backend
 */
export async function getAgentTypes(): Promise<ApiResponse<{agent_types: string[]}>> {
  return await fetchData<{agent_types: string[]}>('/agent/types');
}

/**
 * Create a new agent of the specified type
 */
export async function createAgent(
  agentType: string, 
  config?: AgentConfig, 
  name?: string
): Promise<ApiResponse<{agent_id: string}>> {
  return await postData('/agent/create', {
    agent_type: agentType,
    config: config || {},
    name: name
  });
}

/**
 * Delete an existing agent
 */
export async function deleteAgent(agentId: string): Promise<ApiResponse> {
  return await deleteData(`/agent/${agentId}`);
}

/**
 * Start a specific agent
 */
export async function startAgent(agentId: string): Promise<ApiResponse> {
  return await postData(`/agent/${agentId}/start`, {});
}

/**
 * Stop a specific agent
 */
export async function stopAgent(agentId: string): Promise<ApiResponse> {
  return await postData(`/agent/${agentId}/stop`, {});
}

/**
 * Get status for a specific agent
 */
export async function getAgentStatus(agentId: string): Promise<ApiResponse<AgentStatus>> {
  return await fetchData<AgentStatus>(`/agent/${agentId}/status`);
}

/**
 * Send a query to a specific agent
 */
export async function queryAgent(agentId: string, prompt: string): Promise<ApiResponse<AgentResponse>> {
  return await postData<{prompt: string}, AgentResponse>(`/agent/${agentId}/query`, { prompt });
}
