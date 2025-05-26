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
    setRunningStep(stepId);
    addToast(`Initiating run for step: ${stepId}...`, 'info');
    let success = false;
    let finalUpdatedSteps: Step[] = steps; // Default to current steps in case of early error

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps/${stepId}/run`, {
        method: 'POST',
      });

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
        throw new Error(errorMessage);
      }

      const resultData = await response.json();
      // Use steps from response if available, as it's the most current state after the run action
      if (resultData.steps) {
        finalUpdatedSteps = resultData.steps;
        setSteps(finalUpdatedSteps); // Ensure the hook's state is updated
      } else {
        // Fallback to refreshSteps if backend didn't send the steps array for some reason
        finalUpdatedSteps = await refreshSteps(); // refreshSteps calls setSteps internally
      }

      const stepNameFromState = finalUpdatedSteps.find(s => s.id === stepId)?.name || stepId;

      // Check the 'status' field in the main body of resultData for overall API call success,
      // and then use finalUpdatedSteps for specific step status.
      if (resultData.status === 'success') {
        // The API call itself was successful, now check the actual step's status from finalUpdatedSteps
        const currentStepData = finalUpdatedSteps.find(s => s.id === stepId);
        if (currentStepData?.status === 'completed' || currentStepData?.status === 'in_progress' || currentStepData?.status === 'waiting_input') {
          addToast(`Step "${stepNameFromState}" processed. Current status: ${currentStepData.status}.`, 'success');
          success = true;
        } else if (currentStepData?.status === 'failed') {
          addToast(`Step "${stepNameFromState}" failed. ${resultData.message || ''}`, 'error');
          success = false;
        } else {
           addToast(`Step "${stepNameFromState}" run initiated. Status: ${currentStepData?.status || 'unknown'}. ${resultData.message || ''}`, 'info');
           success = true; // Or false, depending on how to interpret 'pending' or 'waiting_dependency' after a run command
        }
      } else { // resultData.status was 'error' or not 'success'
        addToast(`Failed to process step "${stepNameFromState}". ${resultData.error || 'Unknown error from server.'}`, 'error');
        success = false;
      }
    } catch (err: any) {
      const stepNameFromState = finalUpdatedSteps.find(s => s.id === stepId)?.name || stepId; // Use potentially updated steps for name
      console.error(`Error running step "${stepId}":`, err);
      addToast(`Error initiating run for step "${stepNameFromState}": ${err.message}`, 'error');
      success = false;
      // Ensure steps are refreshed even on error to get latest state if possible
      try {
        finalUpdatedSteps = await refreshSteps(); // refreshSteps calls setSteps
      } catch (refreshError) {
        console.error('Failed to refresh steps after run error:', refreshError);
        // Keep finalUpdatedSteps as they were or set to current `steps` state
        // setSteps might have already been called by the refreshSteps above if it didn't throw
      }
    } finally {
      setRunningStep(null);
    }
    return { success, updatedSteps: finalUpdatedSteps };
  }, [addToast, refreshSteps, steps, setSteps]); // Added setSteps to dependency array
  
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
  };
}
