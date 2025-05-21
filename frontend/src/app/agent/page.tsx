"use client";

import { useState, useEffect } from "react";
import AgentStepExecution from "@/components/AgentStepExecution";
import {
  usePipelineSubscription,
  usePipelinesListSubscription,
  initializeSocket,
} from "@/lib/websocket";
import { api } from "@/lib/api";
import { useStepProgressManager, PipelineData, PipelineStep } from "@/lib/pipelineUtils";
import { COUNTER_KEY } from "@/lib/constants";
import { useForceUpdate, triggerUpdate, startAutoUpdates } from "@/lib/updateManager";
import { useGlobalCounter } from "@/lib/counterUtils";
import { ToastContainer, useToast } from "@/components/Toast";
import AcknowledgmentModal from "@/components/AcknowledgmentModal";
import { useAcknowledgmentHistory } from "@/lib/acknowledgmentHistory";
import AcknowledgmentHistory from "@/components/AcknowledgmentHistory";
import BatchAcknowledgmentModal from "@/components/BatchAcknowledgmentModal";

interface Step {
  status: "pending" | "running" | "completed" | "failed" | "waiting_for_acknowledgment";
  message: string;
  updated_at: number;
  data?: any;
  requires_acknowledgment?: boolean;
}

interface Pipeline {
  id: string;
  agent_name: string;
  status: "initialized" | "in_progress" | "completed" | "failed";
  created_at: number;
  completed_steps: number;
  total_steps: number;
  steps: Record<string, Step>;
}

export default function AgentPage() {
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(null);
  const [isExecutingAllSteps, setIsExecutingAllSteps] = useState<boolean>(false);
  const [availableSteps, setAvailableSteps] = useState<string[]>([]);
  const [isAcknowledging, setIsAcknowledging] = useState<boolean>(false);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [selectedStep, setSelectedStep] = useState<string>("");
  const [batchModalOpen, setBatchModalOpen] = useState<boolean>(false);
  const [stepsToAcknowledge, setStepsToAcknowledge] = useState<string[]>([]);
  
  // Use toast notifications
  const toast = useToast();
  
  // Use acknowledgment history
  const acknowledgmentHistory = useAcknowledgmentHistory(selectedPipeline || undefined);

  // Use the StepProgressManager for tracking execution progress
  const stepManager = useStepProgressManager(selectedPipeline || "", availableSteps);

  // Use WebSocket subscriptions instead of manual HTTP polling
  const {
    pipelines,
    loading: pipelinesLoading,
    updateCounter: pipelinesUpdateCounter,
  } = usePipelinesListSubscription();
  const {
    pipelineData,
    loading,
    updateCounter: pipelineUpdateCounter,
  } = usePipelineSubscription(selectedPipeline);

  // Fetch available steps when component mounts
  useEffect(() => {
    const fetchSteps = async () => {
      try {
        const data = await api.get<{ steps: string[] }>("/api/steps");
        setAvailableSteps(data.steps);
        // Update step manager with available steps
        if (data.steps.length > 0 && stepManager) {
          stepManager.setAvailableSteps(data.steps);
        }
      } catch (err) {
        console.error("Failed to fetch available steps", err);
      }
    };

    fetchSteps();
  }, []);

  // Initialize WebSocket connection when component mounts
  useEffect(() => {
    initializeSocket();
  }, []);

  // Debug logging for pipelines list updates
  useEffect(() => {
    if (pipelines.length > 0) {
      console.log("Pipelines list updated:", {
        count: pipelines.length,
        updateCounter: pipelinesUpdateCounter,
      });
    }
  }, [pipelines, pipelinesUpdateCounter]);

  // Helper function to normalize pipeline data from WebSocket to match PipelineData
  const normalizePipelineData = (pipeline: Pipeline): Partial<PipelineData> => {
    if (!pipeline) return {};
    
    const normalizedSteps: Record<string, PipelineStep> = {};
    
    // Convert Step objects to PipelineStep objects
    if (pipeline.steps) {
      Object.entries(pipeline.steps).forEach(([key, step]) => {
        normalizedSteps[key] = {
          name: key,  // Add the key as the name
          status: step.status,
          message: step.message,
          data: step.data,
          updated_at: step.updated_at,
          timestamp: step.updated_at * 1000 // Convert seconds to milliseconds for timestamp
        };
      });
    }
    
    return {
      id: pipeline.id,
      agent_name: pipeline.agent_name,
      status: pipeline.status,
      created_at: pipeline.created_at,
      total_steps: pipeline.total_steps,
      completed_steps: pipeline.completed_steps,
      steps: normalizedSteps,
      lastUpdated: Date.now()
    };
  };

  // Update step manager when pipeline data changes
  useEffect(() => {
    if (pipelineData && stepManager) {
      const normalizedData = normalizePipelineData(pipelineData);
      stepManager.updatePipelineData(normalizedData);
    }
  }, [pipelineData, stepManager]);

  // Polling fallback for pipeline data in case WebSocket fails
  useEffect(() => {
    if (!selectedPipeline) return;

    // Poll every 3 seconds as a fallback
    const pollingInterval = setInterval(async () => {
      try {
        // Use the API to fetch the latest data
        const freshData = await api.agent.getPipelineStatus(selectedPipeline);
        console.log("Polling fallback: Fetched pipeline data");
      } catch (err) {
        console.error("Polling fallback: Error fetching pipeline data", err);
      }
    }, 3000);

    return () => clearInterval(pollingInterval);
  }, [selectedPipeline]); // Polling fallback for pipelines list in case WebSocket fails
  useEffect(() => {
    // Poll every 5 seconds as a fallback
    const pollingInterval = setInterval(async () => {
      try {
        // Use the API to fetch the latest pipelines list
        await api.agent.listPipelines();
        console.log("Polling fallback: Fetched pipelines list");
      } catch (err) {
        console.error("Polling fallback: Error fetching pipelines list", err);
      }
    }, 5000);

    return () => clearInterval(pollingInterval);
  }, []);

  // Auto-scroll to the selected pipeline and highlight it with animation
  useEffect(() => {
    if (selectedPipeline) {
      const pipelineElement = document.getElementById(
        `pipeline-${selectedPipeline}`
      );
      if (pipelineElement) {
        // First scroll to the element to make sure it's visible
        pipelineElement.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });

        // Add a highlight animation
        pipelineElement.classList.add("animate-pulse");

        // Remove the animation after 2 seconds
        const timeoutId = setTimeout(() => {
          pipelineElement.classList.remove("animate-pulse");
        }, 2000);

        return () => clearTimeout(timeoutId);
      }
    }
  }, [selectedPipeline, pipelines.length]);

  // Debug logging for pipeline data updates
  useEffect(() => {
    if (pipelineData) {
      console.log("Pipeline data updated:", {
        id: pipelineData.id,
        status: pipelineData.status,
        completedSteps: pipelineData.completed_steps,
        totalSteps: pipelineData.total_steps,
        steps: Object.keys(pipelineData.steps || {}).length,
        updateCounter: pipelineUpdateCounter,
      });
    }
  }, [pipelineData, pipelineUpdateCounter]);

  // Get status color based on status
  const getStatusColor = (status: string): string => {
    switch (status) {
      case "success":
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "running":
        return "bg-blue-500";
      case "in_progress":
        return "bg-blue-500";
      case "initialized":
        return "bg-gray-400";
      case "pending":
        return "bg-gray-300";
      case "waiting_for_acknowledgment":
        return "bg-yellow-500";
      default:
        return "bg-gray-300";
    }
  };

  // Format timestamp to readable date
  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Get steps array from steps object, sorted by creation time
  const getOrderedSteps = (): [string, Step][] => {
    if (!pipelineData?.steps) return [];

    // Cache this computation with useMemo
    // First convert to array of entries and explicitly cast to [string, Step][]
    const entries = Object.entries(pipelineData.steps) as [string, Step][];

    // Sort by updated_at timestamp, with fallback to step name for consistent ordering
    return entries.sort((a, b) => {
      const stepATime = a[1].updated_at || 0;
      const stepBTime = b[1].updated_at || 0;

      // If timestamps differ significantly (more than 1 second), use timestamp order
      if (Math.abs(stepATime - stepBTime) > 1) {
        return stepATime - stepBTime;
      }

      // For steps updated at the same time, sort alphabetically by step name
      // This ensures consistent ordering when multiple steps are added simultaneously
      return a[0].localeCompare(b[0], undefined, {
        numeric: true,
        sensitivity: "base",
      });
    });
  };

  // Add a debug component to show the counter
  const DebugCounter = ({ value, label }: { value: number, label: string }) => {
    return (
      <div className="text-xs text-gray-400 absolute top-1 right-1">
        {label}: {value}
      </div>
    );
  };

  // Add a periodic refresh for pipeline details
  useEffect(() => {
    if (pipelineData && !isExecutingAllSteps) {
      // Create a timer that forces a counter update every 2 seconds
      const refreshTimer = setInterval(() => {
        // This will directly increment the counter to force a re-render
        // without having to refetch data from the server
        const event = new CustomEvent('pipeline-counter-update');
        window.dispatchEvent(event);
      }, 2000);
      
      return () => clearInterval(refreshTimer);
    }
  }, [pipelineData, isExecutingAllSteps]);

  // Use our force update mechanism for both pipeline and pipelines
  const pipelineForceUpdateKey = useForceUpdate('pipeline');
  const pipelinesForceUpdateKey = useForceUpdate('pipelines');
  
  // Start auto updates
  useEffect(() => {
    startAutoUpdates();
    
    // Trigger updates every time selected pipeline changes
    if (selectedPipeline) {
      triggerUpdate('pipeline');
    }
  }, [selectedPipeline]);
  
  // Debug logging with update keys visible
  useEffect(() => {
    console.log(`Force update keys: pipeline=${pipelineForceUpdateKey}, pipelines=${pipelinesForceUpdateKey}`);
  }, [pipelineForceUpdateKey, pipelinesForceUpdateKey]);

  // Listen for pipeline update events
  useEffect(() => {
    const handlePipelineUpdate = (event: Event) => {
      const customEvent = event as CustomEvent;
      console.log('Pipeline update event received:', customEvent.detail);
      // Force a re-render by increasing our force update key
      if (customEvent.detail.pipelineId === selectedPipeline) {
        triggerUpdate('pipeline');
      } else {
        // Update all pipelines if it's a different pipeline
        triggerUpdate('pipelines');
      }
    };
    
    window.addEventListener('pipeline-update', handlePipelineUpdate);
    
    return () => {
      window.removeEventListener('pipeline-update', handlePipelineUpdate);
    };
  }, [selectedPipeline]);

  // Function to acknowledge a step requiring confirmation
  const acknowledgeStep = async (stepName: string) => {
    setSelectedStep(stepName);
    setModalOpen(true);
  };
  
  // Function to handle the actual acknowledgment with optional comment
  const handleAcknowledge = async (comment: string) => {
    if (!selectedPipeline || !selectedStep) return;
    
    setIsAcknowledging(true);
    
    try {
      // Call the API endpoint to acknowledge the step with optional comment
      const response = await api.agent.acknowledgeStep(selectedPipeline, selectedStep, comment);
      
      console.log(`Step '${selectedStep}' acknowledged successfully:`, response);
      
      // Record in acknowledgment history
      acknowledgmentHistory.addRecord(selectedStep, selectedPipeline, comment);
      
      // Show success toast notification
      toast.addSuccess(`Step '${selectedStep}' acknowledged successfully`);
      
      // Manually update the UI to reflect the change immediately
      triggerUpdate('pipeline');
      
      // Close the modal
      setModalOpen(false);
      
    } catch (error) {
      console.error(`Error acknowledging step ${selectedStep}:`, error);
      
      // Show error toast notification
      toast.addError(`Failed to acknowledge step: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsAcknowledging(false);
    }
  };
  
  // Function to handle batch acknowledgment with optional comment
  const handleBatchAcknowledge = async (comment: string) => {
    if (!selectedPipeline || stepsToAcknowledge.length === 0) return;
    
    setIsAcknowledging(true);
    
    try {
      // Process each step sequentially
      for (const stepName of stepsToAcknowledge) {
        // Call the API endpoint to acknowledge the step with optional comment
        const response = await api.agent.acknowledgeStep(selectedPipeline, stepName, comment);
        
        console.log(`Step '${stepName}' acknowledged successfully:`, response);
        
        // Record in acknowledgment history
        acknowledgmentHistory.addRecord(stepName, selectedPipeline, comment);
      }
      
      // Show success toast notification
      toast.addSuccess(`${stepsToAcknowledge.length} steps acknowledged successfully`);
      
      // Manually update the UI to reflect the change immediately
      triggerUpdate('pipeline');
      
      // Close the modal and reset selected steps
      setBatchModalOpen(false);
      setStepsToAcknowledge([]);
      
    } catch (error) {
      console.error(`Error acknowledging steps:`, error);
      
      // Show error toast notification
      toast.addError(`Failed to acknowledge steps: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsAcknowledging(false);
    }
  };
  
  // Get all steps that need acknowledgment
  const getPendingAcknowledgmentSteps = (): [string, Step][] => {
    if (!pipelineData?.steps) return [];
    
    return Object.entries(pipelineData.steps)
      .filter(([_, step]) => step.status === "waiting_for_acknowledgment");
  };
  
  // Function to open batch acknowledgment modal if multiple steps need acknowledgment
  const openBatchAcknowledgment = () => {
    const pendingSteps = getPendingAcknowledgmentSteps();
    
    if (pendingSteps.length > 0) {
      setStepsToAcknowledge(pendingSteps.map(([stepName]) => stepName));
      setBatchModalOpen(true);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Agent Pipeline Visualizer</h1>

      {/* Toast notifications container */}
      <ToastContainer messages={toast.messages} onClose={toast.removeMessage} />
      
      {/* Acknowledgment modal */}
      <AcknowledgmentModal
        isOpen={modalOpen}
        stepName={selectedStep}
        onClose={() => setModalOpen(false)}
        onAcknowledge={handleAcknowledge}
        isLoading={isAcknowledging}
      />
      
      {/* Batch acknowledgment modal */}
      <BatchAcknowledgmentModal
        isOpen={batchModalOpen}
        steps={stepsToAcknowledge}
        onClose={() => setBatchModalOpen(false)}
        onAcknowledge={handleBatchAcknowledge}
        isLoading={isAcknowledging}
      />

      <div className="mb-8">
        <AgentStepExecution
          selectedPipelineId={selectedPipeline || undefined}
          onPipelineSelected={(pipelineId) => {
            console.log(`Pipeline selected: ${pipelineId}`);
            setSelectedPipeline(pipelineId);
            stepManager.setPipelineId(pipelineId);
          }}
          onStepExecuted={(data) => {
            // No need for manual refreshes when using WebSockets
            console.log("Step executed via WebSocket");
          }}
          onStepStarted={(stepName) => {
            console.log(`Step started: ${stepName}`);
          }}
          onAllStepsStarted={() => {
            console.log("All steps execution started");
            setIsExecutingAllSteps(true);
            // Make sure StepProgressManager is in sync
            stepManager.startExecutingAllSteps();
          }}
          onAllStepsCompleted={() => {
            console.log("All steps execution completed");
            setIsExecutingAllSteps(false);
            // Make sure StepProgressManager is in sync
            stepManager.stopExecutingAllSteps();
            // Refresh the pipeline data
            if (selectedPipeline) {
              stepManager.fetchPipelineStatus();
            }
          }}
        />
      </div>

      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Available Pipelines</h2>
        {pipelinesLoading ? (
          <div className="flex justify-center my-4">
            <div className="loader">Loading pipelines...</div>
          </div>
        ) : pipelines.length === 0 ? (
          <p className="text-gray-900 font-medium">
            No pipelines available. Start an agent to create a pipeline.
          </p>
        ) : (
          <div
            className="flex flex-wrap gap-4 relative"
            key={`pipelines-wrapper-${pipelinesForceUpdateKey}`}
          >
            <DebugCounter value={pipelinesForceUpdateKey} label="List Updates" />
            {pipelines.map((pipeline: Pipeline) => {
              // Check if this is the currently executing pipeline
              const isExecuting = selectedPipeline === pipeline.id && stepManager.isExecutingAllSteps();
              const executionProgress = isExecuting ? 
                ` (${stepManager.getProgressText()})` : '';
              
              return (
                <button
                  id={`pipeline-${pipeline.id}`}
                  key={`pipeline-${pipeline.id}-${pipelinesForceUpdateKey}`}
                  onClick={() => setSelectedPipeline(pipeline.id)}
                  className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                    selectedPipeline === pipeline.id
                      ? isExecuting 
                        ? "bg-green-600 text-white ring-2 ring-green-300"
                        : "bg-blue-600 text-white ring-2 ring-blue-300"
                      : "bg-gray-200 text-gray-900 hover:bg-gray-300"
                  }`}
                >
                  <div className="font-medium">{pipeline.agent_name}</div>
                  <div className="text-sm">
                    {/* Add key to force re-render */}
                    <span key={`steps-${pipelinesForceUpdateKey}-${pipeline.id}`}>
                      {pipeline.completed_steps}/{pipeline.total_steps} steps{executionProgress}
                    </span>
                  </div>
                  <div
                    className={`text-xs mt-1 px-2 py-1 rounded-full ${
                      isExecuting ? "bg-green-500" : getStatusColor(pipeline.status)
                    } text-white`}
                  >
                    {isExecuting ? "running" : pipeline.status}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {selectedPipeline && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Pipeline Details</h2>
            <div className="text-sm text-gray-500">
              Real-time updates via WebSockets
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center my-8">
              <div className="loader">Loading pipeline details...</div>
            </div>
          ) : pipelineData ? (
            <div
              className="bg-white shadow-lg rounded-lg overflow-hidden relative"
              key={`pipeline-details-${pipelineForceUpdateKey}`}
            >
              <DebugCounter value={pipelineForceUpdateKey} label="Updates" />
              <div className="bg-gray-100 px-6 py-4">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-medium">
                      {pipelineData.agent_name}
                    </h3>
                    <p className="text-gray-900 text-sm">
                      ID: {pipelineData.id}
                    </p>
                    <p className="text-gray-900 text-sm">
                      Created: {formatTimestamp(pipelineData.created_at)}
                    </p>
                    {/* Hidden counter to force re-renders */}
                    <span className="hidden">{pipelineForceUpdateKey}</span>
                  </div>
                  <div
                    className={`px-4 py-2 rounded-full ${
                      stepManager.isExecutingAllSteps() 
                        ? "bg-green-500" 
                        : getStatusColor(pipelineData.status)
                    } text-white`}
                    key={`status-${pipelineForceUpdateKey}`}
                  >
                    {stepManager.isExecutingAllSteps() 
                      ? `Running ${stepManager.getProgressText()}`
                      : pipelineData.status}
                  </div>
                </div>
                <div className="mt-2">
                  {/* Progress bar with key to force re-render */}
                  <div className="w-full bg-gray-300 rounded-full h-2.5 mb-1" key={`progress-${pipelineForceUpdateKey}`}>
                    <div
                      className={`h-2.5 rounded-full ${
                        stepManager.isExecutingAllSteps() 
                          ? "bg-green-500" 
                          : getStatusColor(pipelineData.status)
                      }`}
                      style={{
                        width: `${
                          stepManager.isExecutingAllSteps()
                            ? stepManager.getProgressPercentage()
                            : (pipelineData.completed_steps / pipelineData.total_steps) * 100
                        }%`,
                      }}
                    />
                  </div>
                  <p className="text-sm text-right text-gray-900 font-medium" key={`progress-text-${pipelineForceUpdateKey}`}>
                    <span className="inline-block">{stepManager.isExecutingAllSteps()
                      ? stepManager.getProgressText()
                      : `${pipelineData.completed_steps} of ${pipelineData.total_steps} steps completed`}</span>
                  </p>
                </div>
              </div>

              <div className="px-6 py-4">
                <h4 className="font-semibold mb-4 text-gray-900">
                  Pipeline Steps {/* Add update counter inline to force re-renders */}
                  <span className="hidden" key={`force-update-${pipelineForceUpdateKey}`}>{pipelineForceUpdateKey}</span>
                  
                  {/* Display hint for steps requiring acknowledgement */}
                  {getOrderedSteps().some(([_, step]) => step.status === "waiting_for_acknowledgment") && (
                    <div className="flex items-center mt-2">
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full flex items-center">
                        <span className="mr-1">⚠</span> Steps require acknowledgement
                      </span>
                      
                      {/* Show batch acknowledge button if multiple steps need acknowledgment */}
                      {getPendingAcknowledgmentSteps().length > 1 && (
                        <button
                          onClick={openBatchAcknowledgment}
                          disabled={isAcknowledging}
                          className="ml-2 bg-yellow-600 text-white py-1 px-3 rounded text-xs hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                          Batch Acknowledge ({getPendingAcknowledgmentSteps().length})
                        </button>
                      )}
                    </div>
                  )}
                </h4>
                {/* Update counter used to force re-renders */}
                <div className="space-y-6" key={`steps-wrapper-${pipelineForceUpdateKey}`}>
                  {getOrderedSteps().map(([stepName, step], index) => (
                    <div
                      key={`${stepName}-${step.status || "pending"}-${pipelineForceUpdateKey}`}
                      className={`relative ${step.status === "waiting_for_acknowledgment" ? "bg-yellow-50 border-l-4 border-yellow-500 pl-2 rounded-l pulse-yellow" : ""}`}
                    >
                      {/* Connecting line */}
                      {index < getOrderedSteps().length - 1 && (
                        <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-300 -z-10"></div>
                      )}

                      <div className="flex">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            stepManager.isExecutingAllSteps() && 
                            stepManager.getCurrentStepInfo().name === stepName
                              ? "bg-green-500 animate-pulse" 
                              : getStatusColor(step.status)
                          } text-white z-10`}
                        >
                          {stepManager.isExecutingAllSteps() && 
                           stepManager.getCurrentStepInfo().name === stepName
                            ? "►"
                            : step.status === "completed"
                              ? "✓"
                              : step.status === "failed"
                                ? "✗"
                                : step.status === "running"
                                  ? "►"
                                  : step.status === "waiting_for_acknowledgment"
                                    ? "⚠"
                                    : step.status === "pending"
                                      ? "○"
                                      : "○"}
                        </div>
                        <div className="ml-4 flex-1">
                          <div className="flex justify-between">
                            <h5 className="font-semibold capitalize text-gray-900">
                              {stepManager.formatStepName(stepName)}
                            </h5>
                            <span
                              className={`text-xs px-2 py-1 rounded-full ${
                                stepManager.isExecutingAllSteps() && 
                                stepManager.getCurrentStepInfo().name === stepName
                                  ? "bg-green-500 animate-pulse" 
                                  : getStatusColor(step.status)
                              } text-white`}
                            >
                              {stepManager.isExecutingAllSteps() && 
                               stepManager.getCurrentStepInfo().name === stepName
                                ? "executing..."
                                : step.status}
                            </span>
                          </div>
                          <p className="text-gray-900">{step.message}</p>

                          {/* Display acknowledgement button for steps requiring confirmation */}
                          {step.status === "waiting_for_acknowledgment" && (
                            <div className="mt-3">
                              <button
                                onClick={() => acknowledgeStep(stepName)}
                                disabled={isAcknowledging}
                                className="bg-yellow-600 text-white py-1 px-3 rounded hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm flex items-center"
                              >
                                <span className="mr-1">⚠</span>
                                {isAcknowledging && selectedStep === stepName ? "Acknowledging..." : "Acknowledge and Continue"}
                              </button>
                              <p className="text-xs text-yellow-800 mt-1">
                                This step requires your acknowledgment to continue
                              </p>
                            </div>
                          )}

                          {/* Display step data if available */}
                          {step.data && (
                            <div className="mt-2 p-3 bg-gray-900 rounded text-sm text-white">
                              <div className="font-medium mb-1">Data</div>
                              <pre className="whitespace-pre-wrap">
                                {JSON.stringify(step.data, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {getOrderedSteps().length === 0 && (
                  <p className="text-gray-900 italic">
                    No steps have been executed yet.
                  </p>
                )}
              </div>
              
              {/* Display acknowledgment history */}
              <AcknowledgmentHistory pipelineId={selectedPipeline} className="mt-6" />
            </div>
          ) : (
            <div className="text-gray-900 font-medium">
              Select a pipeline to view details
            </div>
          )}
        </div>
      )}
    </div>
  );
}
