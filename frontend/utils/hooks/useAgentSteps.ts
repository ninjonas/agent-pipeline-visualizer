'use client';

import { useState, useCallback, useEffect } from 'react';
import { Step } from '@/types/agent';

export function useAgentSteps() {
  const [steps, setSteps] = useState<Step[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
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
  };
}
