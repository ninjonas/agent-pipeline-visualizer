'use client';

import { useState, useCallback, useEffect } from 'react';
import { Step } from '@/types/agent';
import { useToast } from '@/contexts/ToastContext';

export function useAgentSteps() {
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningStep, setRunningStep] = useState<string | null>(null);
  const { addToast } = useToast();

  const optimisticallyUpdateStepStatus = useCallback((stepId: string, newStatus: Step['status'], message?: string) => {
    setSteps(prevSteps =>
      prevSteps.map(step =>
        step.id === stepId ? { ...step, status: newStatus, message: message || step.message } : step
      )
    );
  }, [setSteps]);

  const refreshSteps = useCallback(async (): Promise<Step[]> => {
    let fetchedSteps: Step[] = [];
    // setLoading(true); // Consider if this is needed on every refresh or just initial
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps`);
      if (!response.ok) {
        throw new Error('Failed to fetch steps');
      }
      const data = await response.json();
      fetchedSteps = data.steps || [];
      setSteps(fetchedSteps);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching steps:', err);
      setError(err.message || 'Failed to fetch agent steps');
      // setSteps([]); // Optionally clear or retain old steps on error
    } finally {
      setLoading(false);
    }
    return fetchedSteps;
  }, [setSteps, setError, setLoading]); // Dependencies for useCallback

  const runStep = useCallback(async (stepId: string): Promise<{ success: boolean, updatedSteps: Step[] }> => {
    // Optimistically set to in_progress
    optimisticallyUpdateStepStatus(stepId, 'in_progress');
    setRunningStep(stepId); // Keep this to disable run button etc.
    addToast(`Initiating run for step: ${stepId}...`, 'info');
    let success = false;
    let finalUpdatedSteps: Step[] = steps; // Initialize with current steps

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps/${stepId}/run`, {
        method: 'POST',
      });

      // Even if the /run call itself fails, we should refresh to get the latest state,
      // as the agent might have started and failed, updating status.json.
      if (!response.ok) {
        let errorMessage = `Failed to run step ${stepId}`;
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (parseError) {
          const errorText = await response.text();
          errorMessage = `Server error for step ${stepId}: ${response.status} ${response.statusText || errorText}`;
        }
        // Don't throw yet, refresh first, then use this error if needed.
        console.error(errorMessage); // Log the initial error
      }

      // ALWAYS refresh steps after a run attempt to get the most authoritative state
      // This state comes from status.json, which the agent updates directly via its own POST.
      finalUpdatedSteps = await refreshSteps(); 

      const currentStepData = finalUpdatedSteps.find(s => s.id === stepId);
      let safeStepName = stepId;
      if (currentStepData?.name) {
        safeStepName = currentStepData.name;
      }
      
      let safeCurrentStatus: Step['status'] = currentStepData?.status || 'unknown' as Step['status'];

      // Determine overall success based on the refreshed step status
      if (safeCurrentStatus === 'completed') {
        addToast(`Step "${safeStepName}" completed successfully.`, 'success');
        success = true;
      } else if (safeCurrentStatus === 'failed') {
        addToast(`Step "${safeStepName}" failed. ${currentStepData?.message || 'Review agent logs.'}` , 'error');
        success = false;
      } else if (safeCurrentStatus === 'in_progress' || safeCurrentStatus === 'waiting_input') {
        addToast(`Step "${safeStepName}" is now ${safeCurrentStatus.replace('_',' ')}.`, 'info');
        success = true; // The run was initiated, step is processing or waiting
      } else {
        // If the /run response was not ok, and status isn't failed/completed, reflect that.
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: "Failed to parse error from run endpoint."}));
            addToast(`Failed to properly initiate step "${safeStepName}". Status: ${safeCurrentStatus}. Error: ${errorData.error || response.statusText}`, 'error');
            success = false;
        } else {
            addToast(`Step "${safeStepName}" has status: ${safeCurrentStatus}.`, 'info');
            success = true; // Default to success if status is unusual but call succeeded
        }
      }

    } catch (err: any) { // Catch errors from fetch itself or from refreshSteps
      let stepNameForCatch = stepId;
      try {
        const step = finalUpdatedSteps.find(s => s.id === stepId); 
        if (step?.name) {
          stepNameForCatch = step.name;
        }
      } catch (e: any) {
         console.warn(`[useAgentSteps] Error converting step.name to string in catch block for step '${stepId}':`, e);
      }
      const errorMessage = err instanceof Error ? err.message : String(err);
      console.error(`Error during runStep for "${stepId}":`, errorMessage);
      addToast(`Error processing step "${stepNameForCatch}": ${errorMessage}`, 'error');
      success = false;
      // Attempt to refresh steps one last time to ensure UI consistency with backend state
      try {
        finalUpdatedSteps = await refreshSteps();
      } catch (refreshError) {
        console.error('Failed to refresh steps after run error:', refreshError);
      }
    } finally {
      setRunningStep(null);
    }
    return { success, updatedSteps: finalUpdatedSteps };
  }, [addToast, refreshSteps, optimisticallyUpdateStepStatus, steps, setSteps]); // Added steps and setSteps
  
  const updateStepOutput = useCallback(async (stepId: string, filePath: string, content: string): Promise<boolean> => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/files`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          path: filePath,
          content,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update file');
      }
      
      return true;
    } catch (err) {
      console.error('Error updating file:', err);
      return false;
    }
  }, []);
  
  // Initial fetch of steps
  useEffect(() => {
    refreshSteps();
  }, [refreshSteps]);
  
  return {
    steps,
    loading,
    error,
    refreshSteps,
    updateStepOutput,
    runStep,
    runningStep,
    optimisticallyUpdateStepStatus, // Add this
  };
}
