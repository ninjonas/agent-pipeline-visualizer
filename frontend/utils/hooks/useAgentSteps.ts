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
  
  const refreshSteps = useCallback(async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps`);
      if (!response.ok) {
        throw new Error('Failed to fetch steps');
      }
      
      const data = await response.json();
      setSteps(data.steps || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching steps:', err);
      setError('Failed to fetch agent steps');
    } finally {
      setLoading(false);
    }
  }, []);
  
  const runStep = useCallback(async (stepId: string): Promise<boolean> => {
    setRunningStep(stepId);
    addToast(`Running step: ${stepId}...`, 'info');
    
    try {
      // Call the backend to execute the step
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps/${stepId}/run`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        // Try to parse as JSON, but handle the case when it's not JSON
        let errorMessage = 'Failed to run step';
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (parseError) {
          // If we can't parse JSON, try to get the text instead
          try {
            const errorText = await response.text();
            errorMessage = `Server error: ${response.status} ${response.statusText}`;
            console.error('Error response text:', errorText);
          } catch (textError) {
            // If we can't even get text, just use the status
            errorMessage = `Server error: ${response.status} ${response.statusText}`;
          }
        }
        throw new Error(errorMessage);
      }
      
      // Refresh steps to get the latest status
      await refreshSteps();
      
      addToast(`Step "${stepId}" completed successfully`, 'success');
      return true;
    } catch (err) {
      console.error('Error running step:', err);
      addToast(`Error running step: ${err}`, 'error');
      return false;
    } finally {
      setRunningStep(null);
    }
  }, [addToast, refreshSteps]);
  
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
