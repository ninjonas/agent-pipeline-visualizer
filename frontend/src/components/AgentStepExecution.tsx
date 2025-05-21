"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { getSocket, initializeSocket } from "@/lib/websocket";
import { useStepProgressManager } from "@/lib/pipelineUtils";

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
  
  // Use the step progress manager instead of tracking current step index directly
  const stepManager = useStepProgressManager(pipelineId, availableSteps);
  
  // Get executingAllSteps state from StepProgressManager
  const executingAllSteps = stepManager.isExecutingAllSteps();

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
        
        // Update result with current status info
        setResult((prevResult: any) => ({
          ...prevResult,
          [data.step]: { status: 'running', started_at: Date.now() },
          _lastStep: data.step,
          _lastUpdate: Date.now(),
          _lastAction: 'started'
        }));
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
          _lastUpdate: Date.now(),
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
  }, [pipelineId]);

  const executeStep = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    // Batch UI state updates to prevent flickering
    setLoading(true);
    setError(null);
    if (!stepManager.isExecutingAllSteps()) {
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
      if (!stepManager.isExecutingAllSteps()) {
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
      if (!stepManager.isExecutingAllSteps()) {
        setLoading(false);
      }
    }
  };

  const executeAllSteps = async () => {
    if (availableSteps.length === 0 || !pipelineId) return;

    // Batch all state updates together to prevent flickering
    setLoading(true);
    setError(null);
    setResult({
      message: "Starting execution of all steps...",
      steps: {},
      _completedSteps: 0,
      _totalSteps: availableSteps.length,
    });
    
    // Start executing all steps in StepProgressManager and reset counter to first step
    stepManager.startExecutingAllSteps();
    
    // Set the current step index to -1 to indicate we're about to start execution
    // This ensures the first moveToNextStep() call will set the index to 0

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
      
      // Update StepProgressManager with pipeline data
      stepManager.updatePipelineData(freshData);
    } catch (error) {
      console.warn("Could not fetch initial pipeline data:", error);
    }

    // Notify parent that we're starting to execute all steps
    if (onAllStepsStarted) {
      onAllStepsStarted();
    }

    console.log("Starting execution of all steps:", availableSteps);

    // Define a variable to track results for all executed steps
    const allResults: Record<string, any> = {};

    try {
      // Make a copy of the steps array to avoid potential closure issues
      const stepsToExecute = [...availableSteps];

      for (let i = 0; i < stepsToExecute.length; i++) {
        // Move to next step in the StepProgressManager and trigger UI updates
        stepManager.moveToNextStep();
        
        // Get the actual step name from the array
        const stepName = stepsToExecute[i];
        console.log(
          `Executing step ${i + 1}/${stepsToExecute.length}: ${stepName}`
        );

        // Update step status to running in StepProgressManager immediately
        // This allows pipeline list and detail views to show the current step
        stepManager.updateStepData(stepName, {
          status: 'running',
          message: `Executing step ${i + 1}/${stepsToExecute.length}...`
        });

        // Notify parent that a step is starting to execute
        if (onStepStarted) {
          onStepStarted(stepName);
        }

        // Execute the step
        try {
          const response = await api.post<any>("/api/agent/execute", {
            pipeline_id: pipelineId,
            step: stepName,
          });

          // Store results to batch update later
          allResults[stepName] = response;

          // Update results state only once per step to reduce re-renders
          setResult((prevResult: any) => ({
            ...prevResult,
            [stepName]: response,
            _lastStep: stepName,
            _lastResponse: response,
          }));
          
          // Update step data in the StepProgressManager
          stepManager.updateStepData(stepName, {
            status: 'completed',
            data: response
          });

          // Notify parent that a step was executed
          if (onStepExecuted) {
            onStepExecuted(response);
          }

          // Short pause between steps for better UI responsiveness
          await new Promise((resolve) => setTimeout(resolve, 500));
        } catch (stepError) {
          // Update step status to failed in StepProgressManager
          stepManager.updateStepData(stepName, {
            status: 'failed',
            error: stepError instanceof Error ? stepError.message : 'Unknown error'
          });
          
          console.error(`Error executing step ${stepName}:`, stepError);
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
      
      // Update pipeline status in StepProgressManager to show completion
      stepManager.updatePipelineData({
        status: 'completed',
        completed_steps: availableSteps.length,
        total_steps: availableSteps.length
      });

      // Make sure all steps are marked as completed
      availableSteps.forEach(stepName => {
        if (!allResults[stepName]) {
          // If somehow we don't have results for a step, mark it as completed anyway
          // This ensures the UI shows all steps as complete
          stepManager.updateStepData(stepName, {
            status: 'completed',
            message: 'Step completed'
          });
        }
      });

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
      
      // Update pipeline status in StepProgressManager to show failure
      // Include the completed steps count to show partial progress
      stepManager.updatePipelineData({
        status: 'failed',
        // Count how many steps have succeeded based on our results
        completed_steps: Object.keys(allResults).length,
        total_steps: availableSteps.length
      });

      // Ensure the UI reflects the current step as failed
      const currentIndex = stepManager.currentStepIndex;
      if (currentIndex >= 0 && currentIndex < availableSteps.length) {
        const failedStepName = availableSteps[currentIndex];
        stepManager.updateStepData(failedStepName, {
          status: 'failed',
          message: err instanceof Error ? err.message : 'Execution failed'
        });
      }

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
      stepManager.stopExecutingAllSteps();
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
      
      // Update StepProgressManager with new pipeline ID
      stepManager.setPipelineId(newPipelineId);
      
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
                {stepManager.formatStepName(s)}
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
              ? `Running ${stepManager.getProgressText()} (${stepManager.getProgressPercentage()}%)`
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
          <ResultDisplay result={result} />
        </div>
      )}
    </div>
  );
}

// Result display component for showing JSON with fixed height and expand functionality
interface ResultDisplayProps {
  result: any;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result }) => {
  const [expanded, setExpanded] = useState(false);
  const [updateKey, setUpdateKey] = useState(0); // For forcing re-renders
  
  // Force a refresh when the result changes and also listen for pipeline updates
  useEffect(() => {
    console.log("Result changed:", result?._lastStep || "initial load");
    setUpdateKey(prev => prev + 1);
    
    // Also listen for pipeline update events to refresh
    const handlePipelineUpdate = () => {
      console.log("Pipeline update event received in ResultDisplay");
      setUpdateKey(prev => prev + 1);
    };
    
    window.addEventListener('pipeline-update', handlePipelineUpdate);
    
    return () => {
      window.removeEventListener('pipeline-update', handlePipelineUpdate);
    };
  }, [result]);
  
  const toggleExpand = () => {
    setExpanded(!expanded);
  };
  
  return (
    <div className="relative">
      <div className={`p-3 bg-gray-800 rounded text-sm text-white ${expanded ? '' : 'max-h-80 overflow-auto'}`}>
        <pre className="whitespace-pre-wrap" key={updateKey}>
          {JSON.stringify(result, null, 2)}
        </pre>
      </div>
      <button 
        onClick={toggleExpand}
        className="mt-2 text-xs bg-gray-600 hover:bg-gray-700 text-white px-2 py-1 rounded"
      >
        {expanded ? 'Collapse' : 'Expand All'}
      </button>
    </div>
  );
};
