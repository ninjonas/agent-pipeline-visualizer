// Track history of step acknowledgments
import { useState, useEffect } from 'react';

export interface AcknowledgmentRecord {
  stepName: string;
  pipelineId: string;
  timestamp: number;
  comment?: string;
  userId?: string; // For future use with user authentication
}

// Simple in-memory storage for acknowledgments
// In a production app, this would be persisted to a database or local storage
let acknowledgmentHistory: AcknowledgmentRecord[] = [];

// Store a new acknowledgment in history
export const addAcknowledgment = (
  stepName: string,
  pipelineId: string,
  comment?: string,
  userId?: string
): void => {
  const record: AcknowledgmentRecord = {
    stepName,
    pipelineId,
    timestamp: Date.now(),
    comment,
    userId
  };
  
  acknowledgmentHistory = [record, ...acknowledgmentHistory];
  
  // Optional: persist to localStorage
  try {
    localStorage.setItem('acknowledgmentHistory', JSON.stringify(acknowledgmentHistory));
  } catch (e) {
    console.error('Failed to save acknowledgment history to localStorage:', e);
  }
};

// Load history from localStorage on initialization
const loadHistoryFromStorage = (): void => {
  try {
    const storedHistory = localStorage.getItem('acknowledgmentHistory');
    if (storedHistory) {
      acknowledgmentHistory = JSON.parse(storedHistory);
    }
  } catch (e) {
    console.error('Failed to load acknowledgment history from localStorage:', e);
  }
};

// Initialize history from storage
if (typeof window !== 'undefined') {
  loadHistoryFromStorage();
}

// Get acknowledgment history
export const getAcknowledgmentHistory = (
  pipelineId?: string,
  stepName?: string
): AcknowledgmentRecord[] => {
  if (pipelineId && stepName) {
    return acknowledgmentHistory.filter(
      record => record.pipelineId === pipelineId && record.stepName === stepName
    );
  }
  
  if (pipelineId) {
    return acknowledgmentHistory.filter(
      record => record.pipelineId === pipelineId
    );
  }
  
  if (stepName) {
    return acknowledgmentHistory.filter(
      record => record.stepName === stepName
    );
  }
  
  return acknowledgmentHistory;
};

// Clear acknowledgment history
export const clearAcknowledgmentHistory = (): void => {
  acknowledgmentHistory = [];
  
  // Clear from localStorage
  try {
    localStorage.removeItem('acknowledgmentHistory');
  } catch (e) {
    console.error('Failed to clear acknowledgment history from localStorage:', e);
  }
};

// Hook for accessing acknowledgment history
export const useAcknowledgmentHistory = (
  pipelineId?: string,
  stepName?: string
) => {
  const [history, setHistory] = useState<AcknowledgmentRecord[]>([]);
  
  useEffect(() => {
    // Initial load
    setHistory(getAcknowledgmentHistory(pipelineId, stepName));
    
    // Create a custom event listener to update history when new acknowledgments are added
    const handleHistoryUpdate = () => {
      setHistory(getAcknowledgmentHistory(pipelineId, stepName));
    };
    
    window.addEventListener('acknowledgment-history-updated', handleHistoryUpdate);
    
    return () => {
      window.removeEventListener('acknowledgment-history-updated', handleHistoryUpdate);
    };
  }, [pipelineId, stepName]);
  
  // Function to add a new acknowledgment
  const addRecord = (
    stepName: string,
    pipelineId: string,
    comment?: string,
    userId?: string
  ) => {
    addAcknowledgment(stepName, pipelineId, comment, userId);
    
    // Dispatch event to update all listeners
    const event = new CustomEvent('acknowledgment-history-updated');
    window.dispatchEvent(event);
  };
  
  return {
    history,
    addRecord,
    clearHistory: () => {
      clearAcknowledgmentHistory();
      const event = new CustomEvent('acknowledgment-history-updated');
      window.dispatchEvent(event);
    }
  };
};
