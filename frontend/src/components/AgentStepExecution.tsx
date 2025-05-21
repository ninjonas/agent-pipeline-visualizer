"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { getSocket, initializeSocket } from "@/lib/websocket";

interface StepExecutionProps {
  onStepExecuted?: (data: any) => void;
  onStepStarted?: (stepName: string) => void;
  onAllStepsStarted?: () => void;
  onAllStepsCompleted?: () => void;
  onPipelineSelected?: (pipelineId: string) => void;
  selectedPipelineId?: string;
}

export default function AgentStepExecution({
  onStepExecuted,
  onStepStarted,
  onAllStepsStarted,
  onAllStepsCompleted,
  onPipelineSelected,
  selectedPipelineId,
}: StepExecutionProps) {
  const [pipelineId, setPipelineId] = useState<string>(
    selectedPipelineId || ""
  );
  const [step, setStep] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [availableSteps, setAvailableSteps] = useState<string[]>([]);
  const [executingAllSteps, setExecutingAllSteps] = useState<boolean>(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(-1);

  // Update internal pipeline ID when selectedPipelineId prop changes
  useEffect(() => {
    if (selectedPipelineId && selectedPipelineId !== pipelineId) {
      setPipelineId(selectedPipelineId);
    }
  }, [selectedPipelineId]);

  useEffect(() => {
    // Initialize WebSocket connection
    const socket = initializeSocket();

    // Setup listeners for socket events relevant to step execution
    const onStepStarted = (data: any) => {
      if (data.pipeline_id === pipelineId) {
        console.log("WebSocket: Step started:", data.step);
      }
    };

    const onStepUpdated = (data: any) => {
      if (data.pipeline_id === pipelineId) {
        console.log(
          "WebSocket: Step updated:",
          data.step,
          data.step_data.status
        );

        // Always update result regardless of which step is currently selected
        // This ensures all steps get updated when pipeline is running
        setResult((prevResult: any) => ({
          ...prevResult,
          [data.step]: data.step_data,
          _lastStep: data.step,
          _lastResponse: data.step_data,
          _pipeline_status: data.pipeline_status,
          _completed_steps: data.completed_steps,
          _total_steps: data.total_steps || prevResult?._total_steps,
        }));
      }
    };

    // Register WebSocket event handlers
    socket.on("step_started", onStepStarted);
    socket.on("step_updated", onStepUpdated);

    const fetchSteps = async () => {
      try {
        const data = await api.get<{ steps: string[] }>("/api/steps");
        setAvailableSteps(data.steps);
        if (data.steps.length > 0) {
          setStep(data.steps[0]);
        }
      } catch (err) {
        setError("Failed to fetch available steps");
        console.error(err);
      }
    };

    fetchSteps();

    // Cleanup function to remove event listeners
    return () => {
      socket.off("step_started", onStepStarted);
      socket.off("step_updated", onStepUpdated);
    };
  }, [pipelineId, executingAllSteps, step]);

  const executeStep = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    // Batch UI state updates to prevent flickering
    setLoading(true);
    setError(null);
    if (!executingAllSteps) {
      setResult(null);
    }

    // Ensure the parent knows which pipeline we're working with
    if (onPipelineSelected && pipelineId) {
      onPipelineSelected(pipelineId);
    }

    // Notify parent that a step is starting to execute
    if (onStepStarted && step) {
      onStepStarted(step);
    }

    try {
      // Make a direct API call to update the step
      const response = await api.post<any>("/api/agent/execute", {
        pipeline_id: pipelineId,
        step: step,
      });

      // Update results state based on execution context
      if (!executingAllSteps) {
        // When executing a single step, replace entire result
        setResult(response);
      } else {
        // When executing all steps, update the specific step result
        setResult((prevResult: any) => ({
          ...prevResult,
          [step]: response,
          _lastStep: step,
          _lastResponse: response,
        }));
      }

      // Notify parent that a step was executed
      if (onStepExecuted) {
        // Add a small delay to prevent UI flickering from rapid state changes
        setTimeout(() => {
          onStepExecuted(response);
        }, 50);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to execute step");
      console.error(err);
    } finally {
      // Only update loading state when not executing all steps
      // to prevent unnecessary re-renders
      if (!executingAllSteps) {
        setLoading(false);
      }
    }
  };

  const executeAllSteps = async () => {
    if (availableSteps.length === 0 || !pipelineId) return;

    // Batch all state updates together to prevent flickering
    setLoading(true);
    setExecutingAllSteps(true);
    setError(null);
    setResult({
      message: "Starting execution of all steps...",
      steps: {},
      _completedSteps: 0,
      _totalSteps: availableSteps.length,
    });

    // Ensure the parent knows which pipeline we're working with
    if (onPipelineSelected && pipelineId) {
      onPipelineSelected(pipelineId);
    }

    // Subscribe to pipeline events via WebSocket to get real-time updates
    const socket = getSocket();
    socket.emit("subscribe_pipeline", { pipeline_id: pipelineId });

    // Get fresh pipeline data to ensure we have the latest state
    try {
      const freshData = await api.agent.getPipelineStatus(pipelineId);
      setResult((prev: any) => ({
        ...prev,
        _initialData: freshData,
        _completedSteps: freshData.completed_steps || 0,
        _totalSteps: freshData.total_steps || availableSteps.length,
      }));
    } catch (error) {
      console.warn("Could not fetch initial pipeline data:", error);
    }

    // Notify parent that we're starting to execute all steps
    if (onAllStepsStarted) {
      onAllStepsStarted();
    }

    console.log("Starting execution of all steps:", availableSteps);

    try {
      // Make a copy of the steps array to avoid potential closure issues
      const stepsToExecute = [...availableSteps];
      const allResults: Record<string, any> = {};

      for (let i = 0; i < stepsToExecute.length; i++) {
        const currentStep = stepsToExecute[i];
        console.log(
          `Executing step ${i + 1}/${stepsToExecute.length}: ${currentStep}`
        );

        // Update current step index without triggering excessive re-renders
        setCurrentStepIndex(i);

        // No need to update step state as it's only used for display
        // and we already have the currentStep variable

        // Execute the current step directly instead of using the executeStep function
        try {
          // Notify parent that a step is starting to execute
          // Use a more efficient approach that doesn't cause a state update in parent
          if (onStepStarted) {
            onStepStarted(currentStep);
          }

          // Execute the step
          const response = await api.post<any>("/api/agent/execute", {
            pipeline_id: pipelineId,
            step: currentStep,
          });

          // Store results to batch update later
          allResults[currentStep] = response;

          // Update results state only once per step to reduce re-renders
          setResult((prevResult: any) => ({
            ...prevResult,
            [currentStep]: response,
            _lastStep: currentStep,
            _lastResponse: response,
          }));

          // Notify parent that a step was executed
          if (onStepExecuted) {
            onStepExecuted(response);
          }

          // Short pause between steps for better UI responsiveness
          await new Promise((resolve) => setTimeout(resolve, 500));
        } catch (stepError) {
          console.error(`Error executing step ${currentStep}:`, stepError);
          throw stepError; // Re-throw to be caught by the outer try/catch
        }
      }

      // All steps executed successfully
      console.log("All steps completed successfully");

      // Update the final result state only once
      setResult((prevResult: any) => ({
        ...prevResult,
        message: "All steps executed successfully!",
        completed: true,
      }));

      // Longer delay before notifying completion to ensure UI stability
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Notify parent that all steps have been executed
      if (onAllStepsCompleted) {
        onAllStepsCompleted();
      }
    } catch (err) {
      console.error("Error during execute all steps:", err);

      // Set the error state only once
      setError(
        err instanceof Error
          ? `Failed during step ${step}: ${err.message}`
          : "Failed to execute all steps"
      );

      // Longer delay before notifying completion
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Even if there was an error, notify parent that execution has completed
      if (onAllStepsCompleted) {
        onAllStepsCompleted();
      }
    } finally {
      // Batch all cleanup operations together
      console.log("Cleaning up after execute all steps");

      // Wait a moment before final state cleanup to prevent UI flicker
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Reset all states in one batch at the end
      setLoading(false);
      setExecutingAllSteps(false);
      setCurrentStepIndex(-1);
    }
  };

  const registerNewPipeline = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.agent.registerPipeline(
        "WebUI",
        availableSteps.length
      );
      const newPipelineId = response.pipeline_id;
      setPipelineId(newPipelineId);
      setResult({
        message: `New pipeline registered with ID: ${newPipelineId}`,
        ...response,
      });

      // Notify parent about the new pipeline so it can be selected in the UI
      if (onPipelineSelected) {
        onPipelineSelected(newPipelineId);
      }

      if (onStepExecuted) {
        onStepExecuted(response);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to register pipeline"
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-900">
        Execute Agent Step
      </h2>

      <div className="mb-6">
        <div className="flex justify-between items-center">
          <label
            htmlFor="pipelineId"
            className="block text-sm font-medium mb-2 text-gray-700"
          >
            Pipeline ID
          </label>
          <button
            onClick={registerNewPipeline}
            disabled={loading}
            className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            Register New Pipeline
          </button>
        </div>
        <input
          id="pipelineId"
          type="text"
          value={pipelineId}
          onChange={(e) => {
            const newId = e.target.value;
            setPipelineId(newId);
            // Also notify parent of manual pipeline ID changes
            if (onPipelineSelected && newId) {
              onPipelineSelected(newId);
            }
          }}
          placeholder="Enter pipeline ID"
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-800"
          disabled={loading}
        />
      </div>

      <form onSubmit={executeStep}>
        <div className="mb-4">
          <label
            htmlFor="step"
            className="block text-sm font-medium mb-2 text-gray-700"
          >
            Step to Execute
          </label>
          <select
            id="step"
            value={step}
            onChange={(e) => setStep(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-800"
            disabled={loading || !pipelineId}
          >
            {availableSteps.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>

        <div className="flex space-x-2">
          <button
            type="submit"
            disabled={loading || !pipelineId}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading && !executingAllSteps ? "Executing..." : "Execute Step"}
          </button>
          <button
            type="button"
            onClick={executeAllSteps}
            disabled={loading || !pipelineId}
            className="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {executingAllSteps
              ? `Running Step ${currentStepIndex + 1}/${
                  availableSteps.length
                }...`
              : "Execute All Steps"}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-100 border-l-4 border-red-500 text-red-700">
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-4">
          <h3 className="font-medium mb-2">Result</h3>
          <div className="p-3 bg-gray-800 rounded text-sm text-white">
            <pre className="whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
