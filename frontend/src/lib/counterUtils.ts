import { useState, useEffect } from 'react';

// Singleton counter for tracking updates across components
let globalUpdateCounter = 0;

// Function to increment global counter and return new value
export const incrementCounter = () => {
  globalUpdateCounter++;
  return globalUpdateCounter;
};

// Get current counter value
export const getCounter = () => globalUpdateCounter;

// Hook to subscribe to counter updates
export const useGlobalCounter = () => {
  const [counter, setCounter] = useState(globalUpdateCounter);
  
  useEffect(() => {
    // Create timer to poll for changes
    const timer = setInterval(() => {
      if (counter !== globalUpdateCounter) {
        setCounter(globalUpdateCounter);
      }
    }, 100);
    
    return () => clearInterval(timer);
  }, [counter]);
  
  return counter;
};

// Exports a key that can be used with React key prop
export const getUpdateKey = (prefix = "update") => {
  return `${prefix}-${incrementCounter()}`;
};
