// WebSocket service using Socket.IO
import { io, Socket } from "socket.io-client";
import { useEffect, useState } from "react";

const BASE_URL = "http://localhost:4000";

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
// Helper to create a reactive state updater
const createReactiveState = () => {
  const [state, setState] = useState<any>(null);
  const [counter, setCounter] = useState<number>(0);

  const updateState = (updater: any) => {
    setState(updater);
    setCounter((c) => c + 1);
  };

  return { state, updateState, counter };
};

export const usePipelineSubscription = (pipelineId: string | null) => {
  const [pipelineData, setPipelineData] = useState<any>(null);
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
          setUpdateCounter((c) => c + 1); // Increment counter to force re-render
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
        // Add an update id to force React to see this as a new object
        setPipelineData({ ...data.pipeline_data, _updateId: Date.now() });
        setUpdateCounter((c) => c + 1); // Increment counter to force re-render
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
        setPipelineData((prev: any) => {
          if (!prev) return null;

          // Create a deep copy with a new reference
          const updatedPipeline = {
            ...prev,
            _updateId: Date.now(), // Add timestamp to force re-render
          };

          // Update the steps object with the new step data
          updatedPipeline.steps = {
            ...updatedPipeline.steps,
            [data.step]: data.step_data,
          };

          // Update the pipeline status and counts
          updatedPipeline.status = data.pipeline_status;
          updatedPipeline.completed_steps = data.completed_steps;
          updatedPipeline.total_steps =
            data.total_steps || updatedPipeline.total_steps;

          setUpdateCounter((c) => c + 1); // Increment counter to force re-render
          return updatedPipeline;
        });
      }
    };

    // Listen for step started events
    const handleStepStarted = (data: any) => {
      if (data.pipeline_id === pipelineId) {
        console.log("WebSocket: Step started:", data.step);
        setPipelineData((prev: any) => {
          if (!prev) return null;

          // Create a deep copy with a new reference
          const updatedPipeline = {
            ...prev,
            _updateId: Date.now(), // Add timestamp to force re-render
          };

          // Update or add the step with 'running' status if it doesn't exist yet
          updatedPipeline.steps = {
            ...updatedPipeline.steps,
            [data.step]: {
              ...updatedPipeline.steps?.[data.step],
              status: "running",
              message: `Running step ${data.step}...`,
              updated_at: data.timestamp || Date.now() / 1000,
            },
          };

          // Update pipeline status to in_progress if not completed or failed
          if (
            updatedPipeline.status !== "completed" &&
            updatedPipeline.status !== "failed"
          ) {
            updatedPipeline.status = "in_progress";
          }

          setUpdateCounter((c) => c + 1); // Increment counter to force re-render
          return updatedPipeline;
        });
      }
    };

    // Debug helper to periodically force refresh
    const intervalId = setInterval(() => {
      if (pipelineData) {
        console.log("Periodic pipeline data refresh");
        setPipelineData((prev: any) =>
          prev ? { ...prev, _updateId: Date.now() } : null
        );
        setUpdateCounter((c: number) => c + 1);
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
  }, [pipelineId]);

  return { pipelineData, loading, error, updateCounter };
};

// Hook for subscribing to all pipelines list
export const usePipelinesListSubscription = () => {
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [updateCounter, setUpdateCounter] = useState<number>(0); // Add counter to force re-renders

  useEffect(() => {
    const socket = getSocket();

    // Subscribe to all pipelines updates
    socket.emit("subscribe_all_pipelines");

    // Fetch initial pipelines list
    const fetchInitialPipelines = async () => {
      try {
        const response = await fetch(
          `http://localhost:4000/api/agent/pipelines`
        );
        if (response.ok) {
          const data = await response.json();
          // Add update ID to each pipeline
          const pipelinesWithIds = data.pipelines.map((p: any) => ({
            ...p,
            _updateId: Date.now(),
          }));
          setPipelines(pipelinesWithIds);
          setUpdateCounter((c) => c + 1); // Increment counter to force re-render
          setLoading(false);
        } else {
          throw new Error(`Failed to fetch pipelines: ${response.status}`);
        }
      } catch (err) {
        console.error("Error fetching initial pipelines:", err);
        setError("Failed to load pipelines");
        setLoading(false);
      }
    };

    fetchInitialPipelines();

    // Listen for pipeline list updates
    const handlePipelinesListUpdate = (data: any) => {
      console.log("WebSocket: Pipelines list update received");
      // Add an update ID to each pipeline to force React to see them as new objects
      const pipelinesWithIds = data.pipelines.map((p: any) => ({
        ...p,
        _updateId: Date.now(),
      }));
      setPipelines(pipelinesWithIds);
      setUpdateCounter((c) => c + 1); // Increment counter to force re-render
      setLoading(false);
      setError(null);
    };

    // Also listen for individual pipeline registrations to update the list
    const handlePipelineRegistered = (data: any) => {
      console.log("WebSocket: Pipeline registered:", data.pipeline_id);
      setPipelines((prev: any[]) => {
        const existingIndex = prev.findIndex((p) => p.id === data.pipeline_id);
        if (existingIndex >= 0) {
          // Update existing pipeline
          const updated = [...prev];
          updated[existingIndex] = {
            id: data.pipeline_id,
            ...data.pipeline_data,
            _updateId: Date.now(), // Add timestamp to force re-render
          };
          setUpdateCounter((c) => c + 1); // Increment counter to force re-render
          return updated;
        } else {
          // Add new pipeline
          const newPipelines = [
            ...prev,
            {
              id: data.pipeline_id,
              ...data.pipeline_data,
              _updateId: Date.now(), // Add timestamp to force re-render
            },
          ];
          setUpdateCounter((c) => c + 1); // Increment counter to force re-render
          return newPipelines;
        }
      });
    };

    // Listen for step updates to update the pipeline list with latest status
    const handleStepUpdate = (data: any) => {
      console.log(
        "WebSocket: Step update affecting pipeline status:",
        data.pipeline_id
      );
      setPipelines((prev: any[]) => {
        const existingIndex = prev.findIndex((p) => p.id === data.pipeline_id);
        if (existingIndex >= 0) {
          // Update existing pipeline with new status and completion count
          const updated = [...prev];
          updated[existingIndex] = {
            ...updated[existingIndex],
            status: data.pipeline_status,
            completed_steps: data.completed_steps,
            total_steps: data.total_steps || updated[existingIndex].total_steps,
            _updateId: Date.now(), // Add timestamp to force re-render
          };
          setUpdateCounter((c) => c + 1); // Increment counter to force re-render
          return updated;
        }
        return prev;
      });
    };

    // Debug helper to periodically force refresh pipelines list
    const intervalId = setInterval(() => {
      if (pipelines.length > 0) {
        console.log("Periodic pipelines list refresh");
        setPipelines((prev: any[]) =>
          prev.map((pipeline) => ({ ...pipeline, _updateId: Date.now() }))
        );
        setUpdateCounter((c: number) => c + 1);
      }
    }, 5000); // Every 5 seconds

    socket.on("pipelines_list_updated", handlePipelinesListUpdate);
    socket.on("pipeline_registered", handlePipelineRegistered);
    socket.on("step_updated", handleStepUpdate);

    // Clean up listeners when component unmounts
    return () => {
      clearInterval(intervalId);
      socket.off("pipelines_list_updated", handlePipelinesListUpdate);
      socket.off("pipeline_registered", handlePipelineRegistered);
      socket.off("step_updated", handleStepUpdate);
    };
  }, []);

  return { pipelines, loading, error, updateCounter };
};
