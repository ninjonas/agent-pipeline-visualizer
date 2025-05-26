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
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to run step');
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
  
  // Check if a step can run based on its dependencies
  const canRunStep = useCallback((stepId: string): boolean => {
    // Find the step in our steps list
    const step = steps.find(s => s.id === stepId);
    if (!step) return false;
    
    // A step can run if it's:
    // 1. In pending, waiting_dependency, or failed state
    // 2. All dependencies have been completed
    
    if (!['pending', 'waiting_dependency', 'failed'].includes(step.status)) {
      return false;
    }
    
    // Check all dependencies are completed
    if (step.dependencies && step.dependencies.length > 0) {
      const dependencySteps = steps.filter(s => step.dependencies.includes(s.id));
      return dependencySteps.every(s => s.status === 'completed');
    }
    
    // No dependencies, so it can run
    return true;
  }, [steps]);
  
  // Initial fetch of steps
  useEffect(() => {
    refreshSteps();
  }, [refreshSteps]);
  
  return {
    steps,
    loading,
    error,
    runningStep,
    refreshSteps,
    updateStepOutput,
    runStep,
    canRunStep,
  };
}
