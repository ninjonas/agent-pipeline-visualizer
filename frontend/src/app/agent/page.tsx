"use client";

import React, { useState, useEffect } from "react";
import AgentStepExecution from "@/components/AgentStepExecution";
import {
  usePipelineSubscription,
  usePipelinesListSubscription,
  initializeSocket,
} from "@/lib/websocket";
import { api } from "@/lib/api";

interface Step {
  status: "pending" | "running" | "completed" | "failed";
  message: string;
  updated_at: number;
  data?: any;
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
  const [isExecutingAllSteps, setIsExecutingAllSteps] =
    useState<boolean>(false);

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

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Agent Pipeline Visualizer</h1>

      <div className="mb-8">
        <AgentStepExecution
          selectedPipelineId={selectedPipeline || undefined}
          onPipelineSelected={(pipelineId) => {
            console.log(`Pipeline selected: ${pipelineId}`);
            setSelectedPipeline(pipelineId);
          }}
          onStepExecuted={() => {
            // No need for manual refreshes when using WebSockets
            console.log("Step executed via WebSocket");
          }}
          onStepStarted={(stepName) => {
            console.log(`Step started: ${stepName}`);
          }}
          onAllStepsStarted={() => {
            console.log("All steps execution started");
            setIsExecutingAllSteps(true);
          }}
          onAllStepsCompleted={() => {
            console.log("All steps execution completed");
            setIsExecutingAllSteps(false);
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
            className="flex flex-wrap gap-4"
            key={`pipelines-wrapper-${pipelinesUpdateCounter}`}
          >
            {pipelines.map((pipeline) => (
              <button
                id={`pipeline-${pipeline.id}`}
                key={`pipeline-${pipeline.id}`}
                onClick={() => setSelectedPipeline(pipeline.id)}
                className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                  selectedPipeline === pipeline.id
                    ? "bg-blue-600 text-white ring-2 ring-blue-300"
                    : "bg-gray-200 text-gray-900 hover:bg-gray-300"
                }`}
              >
                <div className="font-medium">{pipeline.agent_name}</div>
                <div className="text-sm">
                  {pipeline.completed_steps}/{pipeline.total_steps} steps
                </div>
                <div
                  className={`text-xs mt-1 px-2 py-1 rounded-full ${getStatusColor(
                    pipeline.status
                  )} text-white`}
                >
                  {pipeline.status}
                </div>
              </button>
            ))}
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
              className="bg-white shadow-lg rounded-lg overflow-hidden"
              key={`pipeline-details-${pipelineUpdateCounter}`}
            >
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
                    <span className="hidden">{pipelineUpdateCounter}</span>
                  </div>
                  <div
                    className={`px-4 py-2 rounded-full ${getStatusColor(
                      pipelineData.status
                    )} text-white`}
                  >
                    {pipelineData.status}
                  </div>
                </div>
                <div className="mt-2">
                  {/* Update counter forces re-renders */}
                  <div className="w-full bg-gray-300 rounded-full h-2.5 mb-1">
                    <div
                      className={`h-2.5 rounded-full ${getStatusColor(
                        pipelineData.status
                      )}`}
                      style={{
                        width: `${
                          (pipelineData.completed_steps /
                            pipelineData.total_steps) *
                          100
                        }%`,
                      }}
                    />
                    {/* Hidden counter to force re-renders */}
                    <span className="hidden">{pipelineUpdateCounter}</span>
                  </div>
                  <p className="text-sm text-right text-gray-900 font-medium">
                    {pipelineData.completed_steps} of {pipelineData.total_steps}{" "}
                    steps completed
                  </p>
                </div>
              </div>

              <div className="px-6 py-4">
                <h4 className="font-semibold mb-4 text-gray-900">
                  Pipeline Steps
                </h4>
                {/* Update counter used to force re-renders */}
                <div className="space-y-6">
                  {/* Hidden counter to force re-renders */}
                  <span className="hidden">{pipelineUpdateCounter}</span>
                  {getOrderedSteps().map(([stepName, step], index) => (
                    <div
                      key={`${stepName}-${step.status || "pending"}`}
                      className="relative"
                    >
                      {/* Connecting line */}
                      {index < getOrderedSteps().length - 1 && (
                        <div className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-300 -z-10"></div>
                      )}

                      <div className="flex">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${getStatusColor(
                            step.status
                          )} text-white z-10`}
                        >
                          {step.status === "completed"
                            ? "✓"
                            : step.status === "failed"
                            ? "✗"
                            : step.status === "running"
                            ? "►"
                            : step.status === "pending"
                            ? "○"
                            : "○"}
                        </div>
                        <div className="ml-4 flex-1">
                          <div className="flex justify-between">
                            <h5 className="font-semibold capitalize text-gray-900">
                              {stepName.replace(/_/g, " ")}
                            </h5>
                            <span
                              className={`text-xs px-2 py-1 rounded-full ${getStatusColor(
                                step.status
                              )} text-white`}
                            >
                              {step.status}
                            </span>
                          </div>
                          <p className="text-gray-900">{step.message}</p>

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
