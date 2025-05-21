// API service for frontend to communicate with backend
import { useState, useEffect } from "react";

type ApiResponse<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

export const useApi = <T>(url: string): ApiResponse<T> => {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`http://localhost:4000${url}`);

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

    fetchData();
  }, [url]);

  return { data, error, loading };
};

export const api = {
  get: async <T>(url: string): Promise<T> => {
    const response = await fetch(`http://localhost:4000${url}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    return response.json();
  },

  post: async <T>(url: string, data: any): Promise<T> => {
    const response = await fetch(`http://localhost:4000${url}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  },

  // Agent-specific API functions
  agent: {
    // List all agent pipelines
    listPipelines: async () => {
      return api.get<{ pipelines: any[] }>("/api/agent/pipelines");
    },

    // Get status of a specific pipeline
    getPipelineStatus: async (pipelineId: string) => {
      return api.get<any>(`/api/agent/status/${pipelineId}`);
    },

    // Register a new pipeline
    registerPipeline: async (agentName: string, totalSteps: number) => {
      return api.post<{ pipeline_id: string }>("/api/agent/register", {
        agent_name: agentName,
        total_steps: totalSteps,
      });
    },

    // Update a pipeline step
    updateStep: async (
      pipelineId: string,
      step: string,
      status: string,
      message: string,
      data?: any
    ) => {
      const payload: any = {
        pipeline_id: pipelineId,
        step,
        status,
        message,
      };

      if (data !== undefined) {
        payload.data = data;
      }

      return api.post<{ status: string }>("/api/agent/update", payload);
    },

    // Acknowledge a step that requires user confirmation
    acknowledgeStep: async (pipelineId: string, step: string, comment?: string) => {
      return api.post<{ status: string, message: string, pipeline_id: string, step: string }>(
        "/api/agent/acknowledge", 
        {
          pipeline_id: pipelineId,
          step,
          comment
        }
      );
    },
  },
};
