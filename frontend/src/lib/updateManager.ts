// Create a simple event-based update system
import { useState, useEffect } from 'react';

let updateListeners: Record<string, Set<Function>> = {
  'global': new Set(),
  'pipeline': new Set(),
  'pipelines': new Set(),
  'step': new Set()
};

// Subscribe to updates for a particular target
export const subscribeToUpdates = (target: string, callback: Function) => {
  if (!updateListeners[target]) {
    updateListeners[target] = new Set();
  }
  updateListeners[target].add(callback);
  
  // Return unsubscribe function
  return () => {
    if (updateListeners[target]) {
      updateListeners[target].delete(callback);
    }
  };
};

// Trigger an update for a specific target
export const triggerUpdate = (target: string) => {
  console.log(`Update triggered for: ${target}`);
  
  // Trigger for the specific target
  if (updateListeners[target]) {
    updateListeners[target].forEach(callback => callback());
  }
  
  // Always trigger global updates
  if (target !== 'global') {
    updateListeners['global'].forEach(callback => callback());
  }
};

// Start a timer that periodically triggers updates
let updateIntervalId: number | null = null;

export const startAutoUpdates = (intervalMs: number = 2000) => {
  stopAutoUpdates(); // Clear any existing interval
  
  updateIntervalId = window.setInterval(() => {
    triggerUpdate('global');
  }, intervalMs);
};

export const stopAutoUpdates = () => {
  if (updateIntervalId !== null) {
    clearInterval(updateIntervalId);
    updateIntervalId = null;
  }
};

// React hook to use with the update system
export const useForceUpdate = (target: string = 'global') => {
  const [updateKey, setUpdateKey] = useState(0);
  
  useEffect(() => {
    // Create an update function
    const forceUpdate = () => {
      setUpdateKey(prev => prev + 1);
    };
    
    // Subscribe to updates
    const unsubscribe = subscribeToUpdates(target, forceUpdate);
    
    // Start auto updates when component mounts
    if (target === 'global' && updateIntervalId === null) {
      startAutoUpdates();
    }
    
    // Clean up subscription when component unmounts
    return () => {
      unsubscribe();
    };
  }, [target]);
  
  return updateKey;
};