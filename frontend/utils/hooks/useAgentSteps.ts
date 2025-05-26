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

  const optimisticallyUpdateStepStatus = useCallback((stepId: string, newStatus: Step['status']) => {
    setSteps(prevSteps =>
      prevSteps.map(step =>
        step.id === stepId ? { ...step, status: newStatus } : step
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

      let safeStepName = stepId;
      try {
        const step = finalUpdatedSteps.find(s => s.id === stepId);
        if (step && typeof step.name === 'string') {
          safeStepName = step.name;
        } else if (step && step.name !== null && step.name !== undefined) {
          safeStepName = String(step.name);
        }
      } catch (e: any) {
        console.warn(`[useAgentSteps] Error converting step.name to string for step '${stepId}':`, e);
        safeStepName = `${stepId} (name error: ${e.message || 'unknown'})`;
      }

      if (resultData.status === 'success') {
        const currentStepData = finalUpdatedSteps.find(s => s.id === stepId);
        let safeCurrentStatus = 'unknown';
        if (currentStepData && typeof currentStepData.status === 'string') {
          safeCurrentStatus = currentStepData.status;
        } else if (currentStepData && currentStepData.status !== null && currentStepData.status !== undefined) {
          try {
            safeCurrentStatus = String(currentStepData.status);
          } catch (e: any) {
            console.warn(`[useAgentSteps] Error converting currentStepData.status to string for step '${stepId}':`, e);
            safeCurrentStatus = `(status error: ${e.message || 'unknown'})`;
          }
        }

        if (safeCurrentStatus === 'completed' || safeCurrentStatus === 'in_progress' || safeCurrentStatus === 'waiting_input') {
          addToast(`Step "${safeStepName}" processed. Current status: ${safeCurrentStatus}.`, 'success');
          success = true;
        } else if (safeCurrentStatus === 'failed') {
          let safeResultMessage = '';
          if (resultData && resultData.hasOwnProperty('message')) {
            const rawMessage = resultData.message;
            if (typeof rawMessage === 'string') {
              safeResultMessage = rawMessage;
            } else if (rawMessage !== null && rawMessage !== undefined) {
              try {
                safeResultMessage = String(rawMessage);
              } catch (e: any) {
                console.warn(`[useAgentSteps] Error converting resultData.message to string for step '${stepId}' (in failed status block):`, e);
                safeResultMessage = `(error processing message: ${e.message || 'unknown'})`;
              }
            }
          }
          addToast(`Step "${safeStepName}" failed. ${safeResultMessage || ''}`, 'error');
          success = false;
        } else {
           // Safely process resultData.message (already improved by previous fix, ensure consistency)
           let messageText = '';
           if (resultData && resultData.hasOwnProperty('message')) {
             const rawMessage = resultData.message;
             if (typeof rawMessage === 'string') {
               messageText = rawMessage;
             } else if (rawMessage !== null && rawMessage !== undefined) {
               try {
                 messageText = String(rawMessage);
               } catch (e: any) {
                 console.warn(`[useAgentSteps] Error converting resultData.message to string for step '${stepId}':`, e);
                 messageText = `(error processing message: ${e.message || 'unknown'})`;
               }
             }
           }
           addToast(`Step "${safeStepName}" run initiated. Status: ${safeCurrentStatus || 'unknown'}. ${messageText}`, 'info');
           success = true;
        }
      } else { // resultData.status was 'error' or not 'success'
        let safeResultError = 'Unknown error from server.';
        if (resultData && resultData.hasOwnProperty('error')) {
            const rawError = resultData.error;
            if (typeof rawError === 'string') {
                safeResultError = rawError;
            } else if (rawError !== null && rawError !== undefined) {
                try {
                    safeResultError = String(rawError);
                } catch (e: any) {
                    console.warn(`[useAgentSteps] Error converting resultData.error to string for step '${stepId}':`, e);
                    safeResultError = `(error processing server error: ${e.message || 'unknown'})`;
                }
            }
        }
        addToast(`Failed to process step "${safeStepName}". ${safeResultError}`, 'error');
        success = false;
      }
    } catch (err: any) {
      // Ensure safeStepName is defined in this scope for the catch block's addToast
      let stepNameForCatch = stepId;
      try {
        const step = finalUpdatedSteps.find(s => s.id === stepId); // finalUpdatedSteps might be from before error
        if (step && typeof step.name === 'string') {
          stepNameForCatch = step.name;
        } else if (step && step.name !== null && step.name !== undefined) {
          stepNameForCatch = String(step.name);
        }
      } catch (e: any) {
         console.warn(`[useAgentSteps] Error converting step.name to string in catch block for step '${stepId}':`, e);
         stepNameForCatch = `${stepId} (name error in catch: ${e.message || 'unknown'})`;
      }
      console.error(`Error running step "${stepId}":`, err instanceof Error ? err.message : String(err));
      let errorMessageForToast = 'unknown error';
      if (err instanceof Error) {
        errorMessageForToast = err.message;
      } else if (err && err.hasOwnProperty('message')) {
        try {
          errorMessageForToast = String(err.message);
        } catch (e: any) {
          errorMessageForToast = `(error processing error message: ${e.message || 'unknown'})`;
        }
      } else {
        try {
          errorMessageForToast = String(err);
        } catch (e: any) {
          errorMessageForToast = `(error converting error to string: ${e.message || 'unknown'})`;
        }
      }
      addToast(`Error initiating run for step "${stepNameForCatch}": ${errorMessageForToast}`, 'error');
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
    optimisticallyUpdateStepStatus, // Add this
  };
}
