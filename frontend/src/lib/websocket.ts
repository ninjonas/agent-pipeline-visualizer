// WebSocket service using Socket.IO
import { io, Socket } from "socket.io-client";
import { useEffect, useState } from "react";
import { COUNTER_KEY } from "./constants";
import { triggerUpdate } from "./updateManager";

const BASE_URL = "http://localhost:4000";

// Type definitions for clarity
export interface Step {
  status: "pending" | "running" | "completed" | "failed";
  message: string;
  updated_at: number;
  data?: any;
}

export interface Pipeline {
  id: string;
  agent_name: string;
  status: "initialized" | "in_progress" | "completed" | "failed";
  created_at: number;
  completed_steps: number;
  total_steps: number;
  steps: Record<string, Step>;
  _updateId?: number;
  _forcedUpdate?: number;
  [COUNTER_KEY]?: number;
}

// Singleton socket instance
let socket: Socket;

// Initialize the socket connection
export const initializeSocket = (): Socket => {
  if (!socket) {
    const socketOptions = {
      transports: ["websocket"],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    };

    socket = io(BASE_URL, socketOptions);

    socket.on("connect", () => {
      console.log("WebSocket connected");
    });

    socket.on("reconnect", (attemptNumber) => {
      console.log(`WebSocket reconnected after ${attemptNumber} attempts`);
    });

    socket.on("reconnect_attempt", (attemptNumber) => {
      console.log(`WebSocket reconnection attempt #${attemptNumber}`);
    });

    socket.on("reconnect_failed", () => {
      console.error("WebSocket reconnection failed after max attempts");
    });

    socket.on("disconnect", (reason) => {
      console.log(`WebSocket disconnected: ${reason}`);
      if (reason === "io server disconnect") {
        // The server disconnected the client
        socket.connect();
      }
    });

    socket.on("error", (error) => {
      console.error("WebSocket error:", error);
    });
  }
  return socket;
};

// Get the existing socket or create a new one
export const getSocket = (): Socket => {
  // If socket isn't initialized yet, initialize it
  if (!socket) {
    return initializeSocket();
  }
  return socket;
};

// Hook for subscribing to pipeline updates
export const usePipelineSubscription = (pipelineId: string | null) => {
  const [pipelineData, setPipelineData] = useState<Pipeline | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updateCounter, setUpdateCounter] = useState<number>(0); // Add counter to force re-renders

  useEffect(() => {
    if (!pipelineId) {
      setPipelineData(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    const socket = getSocket();

    // Fetch initial pipeline data
    const fetchInitialData = async () => {
      try {
        // Subscribe to specific pipeline updates
        socket.emit("subscribe_pipeline", { pipeline_id: pipelineId });

        // Fetch current pipeline state to ensure we have the latest data
        const response = await fetch(
          `http://localhost:4000/api/agent/status/${pipelineId}`
        );
        if (response.ok) {
          const data = await response.json();
          setPipelineData({ ...data, _updateId: Date.now() }); // Add timestamp to force re-render
          setUpdateCounter((c: number) => c + 1); // Increment counter to force re-render
          setLoading(false);
          setError(null);
        } else {
          throw new Error(`Failed to fetch pipeline data: ${response.status}`);
        }
      } catch (err) {
        console.error("Error fetching initial pipeline data:", err);
        setError("Failed to load pipeline data");
        setLoading(false);
      }
    };

    fetchInitialData();

    // Listen for pipeline updates
    const handlePipelineUpdate = (data: any) => {
      if (data.pipeline_id === pipelineId) {
        console.log("WebSocket: Full pipeline update received");
        
        // First update the pipeline data with the new data
        const updateId = Date.now();
        setPipelineData({ 
          ...data.pipeline_data, 
          _updateId: updateId
        });
        
        // Then separately update the counter to trigger re-renders
        setUpdateCounter(prevCounter => {
          const newCounter = prevCounter + 1;
          console.log(`Pipeline update counter: ${prevCounter} → ${newCounter}`);
          return newCounter;
        });
        
        setLoading(false);
        setError(null);
      }
    };

    // Listen for step updates
    const handleStepUpdate = (data: any) => {
      if (data.pipeline_id === pipelineId) {
        console.log(
          "WebSocket: Step update received:",
          data.step,
          data.pipeline_status
        );
        
        // Update pipeline data without depending on the counter state
        setPipelineData((prev: Pipeline | null) => {
          if (!prev) return null;

          // Create a deep copy with a new reference
          const updatedPipeline = {
            ...prev,
            _updateId: Date.now()
          };

          // Update the steps object with the new step data
          updatedPipeline.steps = {
            ...updatedPipeline.steps,
            [data.step]: data.step_data,
          };

          // Update the pipeline status and counts
          updatedPipeline.status = data.pipeline_status;
          updatedPipeline.completed_steps = data.completed_steps;
          updatedPipeline.total_steps = data.total_steps || updatedPipeline.total_steps;

          return updatedPipeline;
        });
        
        // Separately update the counter to trigger re-renders
        setUpdateCounter(prevCounter => {
          const newCounter = prevCounter + 1;
          console.log(`Step update counter: ${prevCounter} → ${newCounter}`);
          return newCounter;
        });
      }
    };

    // Listen for step started events
    const handleStepStarted = (data: any) => {
      if (data.pipeline_id === pipelineId) {
        console.log("WebSocket: Step started:", data.step);
        
        // Update pipeline data
        setPipelineData((prev: Pipeline | null) => {
          if (!prev) return null;

          // Create a deep copy with a new reference
          const updatedPipeline = {
            ...prev,
            _updateId: Date.now(),
            // Update step information
            steps: {
              ...prev.steps,
              [data.step]: {
                ...prev.steps?.[data.step],
                status: "running",
                message: `Running step ${data.step}...`,
                updated_at: data.timestamp || Date.now() / 1000,
              },
            }
          };

          // Update pipeline status to in_progress if not completed or failed
          if (
            updatedPipeline.status !== "completed" &&
            updatedPipeline.status !== "failed"
          ) {
            updatedPipeline.status = "in_progress";
          }

          return updatedPipeline;
        });
        
        // Separately update the counter
        setUpdateCounter((c: number) => c + 1);
      }
    };

    // Debug helper to periodically force refresh
    const intervalId = setInterval(() => {
      // Don't use pipelineData in the dependency of this interval
      // since it will be refreshed from outside
      console.log("Periodic pipeline data refresh");
      // Trigger a counter update without depending on pipelineData
      setUpdateCounter(prevCounter => prevCounter + 1);
      
      // Instead of updating pipelineData here, fetch fresh data from the server
      if (pipelineId) {
        fetch(`http://localhost:4000/api/agent/status/${pipelineId}`)
          .then(response => {
            if (response.ok) return response.json();
            throw new Error(`Failed to refresh pipeline data: ${response.status}`);
          })
          .then(data => {
            setPipelineData({ ...data, _updateId: Date.now() });
          })
          .catch(err => {
            console.error("Error in periodic refresh:", err);
          });
      }
    }, 5000); // Every 5 seconds

    socket.on("pipeline_updated", handlePipelineUpdate);
    socket.on("step_updated", handleStepUpdate);
    socket.on("step_started", handleStepStarted);

    // Clean up listeners when component unmounts or pipelineId changes
    return () => {
      clearInterval(intervalId);
      // Unsubscribe from the pipeline updates
      socket.emit("unsubscribe_pipeline", { pipeline_id: pipelineId });
      // Remove event listeners
      socket.off("pipeline_updated", handlePipelineUpdate);
      socket.off("step_updated", handleStepUpdate);
      socket.off("step_started", handleStepStarted);
    };
  }, [pipelineId]); // Remove pipelineData from dependency array to prevent infinite loops

  // Listen for custom counter update events
  useEffect(() => {
    const handleCounterUpdate = () => {
      setUpdateCounter((prevCounter: number) => prevCounter + 1);
      console.log('Force updating pipeline counter from event');
    };
    
    window.addEventListener('pipeline-counter-update', handleCounterUpdate);
    
    return () => {
      window.removeEventListener('pipeline-counter-update', handleCounterUpdate);
    };
  }, []);

  return { pipelineData, loading, error, updateCounter };
};

// Hook for subscribing to pipelines list updates
export const usePipelinesListSubscription = () => {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updateCounter, setUpdateCounter] = useState<number>(0);

  useEffect(() => {
    const socket = getSocket();

    // Fetch initial pipelines list
    const fetchInitialData = async () => {
      try {
        // Subscribe to pipelines list updates
        socket.emit("subscribe_pipelines_list");

        // Fetch current pipelines list
        const response = await fetch(`http://localhost:4000/api/agent/pipelines`);
        if (response.ok) {
          const data = await response.json();
          setPipelines(data.pipelines || []);
          setUpdateCounter((c: number) => c + 1);
          setLoading(false);
          setError(null);
        } else {
          throw new Error(`Failed to fetch pipelines list: ${response.status}`);
        }
      } catch (err) {
        console.error("Error fetching initial pipelines list:", err);
        setError("Failed to load pipelines list");
        setLoading(false);
      }
    };

    fetchInitialData();

    // Listen for pipelines list updates
    const handlePipelinesListUpdate = (data: any) => {
      console.log("WebSocket: Pipelines list update received");
      setPipelines(data.pipelines || []);
      setUpdateCounter((c: number) => c + 1);
    };

    // Listen for new pipeline creation
    const handlePipelineCreated = (data: any) => {
      console.log("WebSocket: New pipeline created:", data.pipeline_id);
      // Fetch the full pipelines list to make sure we have all the data
      fetchInitialData();
    };

    socket.on("pipelines_list_updated", handlePipelinesListUpdate);
    socket.on("pipeline_created", handlePipelineCreated);

    // Debug helper to periodically force refresh
    const intervalId = setInterval(() => {
      fetchInitialData();
    }, 10000); // Every 10 seconds

    // Clean up listeners when component unmounts
    return () => {
      clearInterval(intervalId);
      socket.off("pipelines_list_updated", handlePipelinesListUpdate);
      socket.off("pipeline_created", handlePipelineCreated);
      socket.emit("unsubscribe_pipelines_list");
    };
  }, []);

  // Listen for custom counter update events
  useEffect(() => {
    const handleCounterUpdate = () => {
      setUpdateCounter((prevCounter: number) => prevCounter + 1);
      console.log('Force updating pipelines list counter from event');
    };
    
    window.addEventListener('pipelines-list-counter-update', handleCounterUpdate);
    
    return () => {
      window.removeEventListener('pipelines-list-counter-update', handleCounterUpdate);
    };
  }, []);

  return { pipelines, loading, error, updateCounter };
};
