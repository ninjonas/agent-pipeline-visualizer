import { getSocket } from './websocket';
import { api } from './api';
import { useState, useEffect } from 'react';
import { triggerUpdate } from './updateManager';

export interface PipelineStep {
  name?: string;  // Make name optional to match Step from websocket.ts
  status: 'pending' | 'running' | 'completed' | 'failed';
  message?: string; // Add message field to match Step from websocket.ts
  data?: any;
  timestamp?: number;
  updated_at?: number; // Add updated_at field to match Step from websocket.ts
}

export interface PipelineData {
  id: string;
  agent_name: string;
  created_at: number;
  status: 'initialized' | 'running' | 'in_progress' | 'completed' | 'failed';
  total_steps: number;
  completed_steps: number;
  steps: Record<string, PipelineStep>;
  currentStepIndex?: number;
  currentStep?: string;
  lastUpdated?: number;
}

/**
 * StepProgressManager - A utility class to manage pipeline step execution progress
 * 
 * This class helps track step execution across components and provides methods to:
 * - Subscribe to step updates from WebSockets
 * - Track the current step during "execute all steps" workflows
 * - Calculate progress percentages
 * - Format step information for display
 */
export class StepProgressManager {
  private pipelineId: string;
  private availableSteps: string[];
  private _currentStepIndex: number = -1;
  private _executingAllSteps: boolean = false;
  private listeners: Set<(data: any) => void> = new Set();
  private pipelineData: Partial<PipelineData> = {};
  
  constructor(pipelineId: string, availableSteps: string[] = []) {
    this.pipelineId = pipelineId;
    this.availableSteps = availableSteps;
    
    // Initialize with basic data
    this.pipelineData = {
      id: pipelineId,
      total_steps: availableSteps.length,
      completed_steps: 0,
      steps: {},
    };
  }
  
  /**
   * Get the current pipeline ID
   */
  getPipelineId(): string {
    return this.pipelineId;
  }
  
  /**
   * Set a new pipeline ID and reset tracking
   */
  setPipelineId(pipelineId: string): void {
    this.pipelineId = pipelineId;
    this.reset();
  }
  
  /**
   * Set the available steps for execution
   */
  setAvailableSteps(steps: string[]): void {
    this.availableSteps = steps;
    this.pipelineData.total_steps = steps.length;
  }
  
  /**
   * Reset the progress manager to initial state
   */
  reset(): void {
    this._currentStepIndex = -1;
    this._executingAllSteps = false;
    this.pipelineData = {
      id: this.pipelineId,
      total_steps: this.availableSteps.length,
      completed_steps: 0,
      steps: {},
    };
  }
  
  /**
   * Start tracking execution of all steps
   */
  startExecutingAllSteps(): void {
    this._executingAllSteps = true;
    this._currentStepIndex = -1;
    
    // Subscribe to pipeline events via WebSocket
    const socket = getSocket();
    socket.emit("subscribe_pipeline", { pipeline_id: this.pipelineId });
  }
  
  /**
   * Stop tracking execution of all steps
   */
  stopExecutingAllSteps(): void {
    this._executingAllSteps = false;
    this._currentStepIndex = -1;
  }
  
  /**
   * Check if execution of all steps is in progress
   */
  isExecutingAllSteps(): boolean {
    return this._executingAllSteps;
  }
  
  /**
   * Move to the next step and return its name
   */
  moveToNextStep(): string | null {
    if (!this._executingAllSteps || this.availableSteps.length === 0) {
      return null;
    }
    
    this._currentStepIndex++;
    
    if (this._currentStepIndex >= this.availableSteps.length) {
      this._executingAllSteps = false;
      this.notifyListeners(this.pipelineData); // Force notification
      return null;
    }
    
    const currentStep = this.availableSteps[this._currentStepIndex];
    this.pipelineData.currentStep = currentStep;
    this.pipelineData.currentStepIndex = this._currentStepIndex;
    
    // Force notification to update UI
    this.pipelineData.lastUpdated = Date.now();
    this.notifyListeners(this.pipelineData);
    
    // Also trigger UI update through the update manager
    triggerUpdate('pipeline');
    
    return currentStep;
  }

  /**
   * Get the current step index
   */
  get currentStepIndex(): number {
    return this._currentStepIndex;
  }

  /**
   * Get the total steps count
   */
  get totalSteps(): number {
    return this.availableSteps.length;
  }
  
  /**
   * Get the current step information
   */
  getCurrentStepInfo(): { index: number; name: string | null; progress: string } {
    return {
      index: this._currentStepIndex,
      name: this._currentStepIndex >= 0 ? this.availableSteps[this._currentStepIndex] : null,
      progress: this.getProgressText(),
    };
  }
  
  /**
   * Normalize status values between different parts of the system
   * 
   * WebSocket uses 'in_progress' while some parts of the system use 'running'
   */
  private normalizeStatus(status: string): 'initialized' | 'running' | 'in_progress' | 'completed' | 'failed' {
    if (status === 'in_progress') return 'running';
    if (status === 'running') return 'running';
    return status as any;
  }

  /**
   * Update pipeline data with new information
   */
  updatePipelineData(data: Partial<PipelineData>): void {
    // Normalize status if present
    const normalizedData = { ...data };
    if (normalizedData.status) {
      normalizedData.status = this.normalizeStatus(normalizedData.status);
    }
    
    this.pipelineData = {
      ...this.pipelineData,
      ...normalizedData,
      lastUpdated: Date.now(),
    };
    
    // Notify listeners about the update
    this.notifyListeners(this.pipelineData);
    
    // Trigger UI update through the update manager
    triggerUpdate('pipeline');
  }
  
  /**
   * Update a specific step's data
   */
  updateStepData(stepName: string, stepData: any): void {
    if (!this.pipelineData.steps) {
      this.pipelineData.steps = {};
    }
    
    this.pipelineData.steps[stepName] = {
      ...this.pipelineData.steps[stepName],
      ...stepData,
      name: stepName,
      timestamp: Date.now(),
    };
    
    // Update completed_steps count based on step statuses
    this.recalculateCompletedSteps();
    
    // Notify listeners
    this.notifyListeners({
      ...this.pipelineData,
      lastUpdated: Date.now(),
    });
    
    // Trigger UI update through the update manager
    triggerUpdate('pipeline');
  }
  
  /**
   * Recalculate how many steps are completed based on their status
   */
  private recalculateCompletedSteps(): void {
    if (!this.pipelineData.steps) return;
    
    let completedCount = 0;
    Object.values(this.pipelineData.steps).forEach(step => {
      if (step.status === 'completed') {
        completedCount++;
      }
    });
    
    this.pipelineData.completed_steps = completedCount;
  }
  
  /**
   * Get the progress percentage (0-100)
   */
  getProgressPercentage(): number {
    const total = this.pipelineData.total_steps || this.availableSteps.length;
    if (total === 0) return 0;
    
    const completed = this.pipelineData.completed_steps || 0;
    return Math.round((completed / total) * 100);
  }
  
  /**
   * Get formatted progress text (e.g., "Step 3/5")
   */
  getProgressText(): string {
    const currentIndex = this._currentStepIndex + 1;
    const total = this.availableSteps.length;
    
    if (this._executingAllSteps && currentIndex > 0) {
      return `Step ${currentIndex}/${total}`;
    }
    
    // If we're tracking overall completion rather than current execution
    const completed = this.pipelineData.completed_steps || 0;
    const totalSteps = this.pipelineData.total_steps || total;
    
    return `${completed}/${totalSteps} steps completed`;
  }
  
  /**
   * Format a step name for display (e.g., convert "update_goal" to "Update Goal")
   */
  formatStepName(stepName: string): string {
    return stepName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  
  /**
   * Get the complete pipeline data
   */
  getPipelineData(): Partial<PipelineData> {
    return this.pipelineData;
  }
  
  /**
   * Add a listener function to be called when pipeline data updates
   */
  addListener(callback: (data: any) => void): void {
    this.listeners.add(callback);
  }
  
  /**
   * Remove a previously added listener
   */
  removeListener(callback: (data: any) => void): void {
    this.listeners.delete(callback);
  }
  
  /**
   * Notify all listeners with the current data
   */
  private notifyListeners(data: any): void {
    this.listeners.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in pipeline data listener:', error);
      }
    });
    
    // Broadcast a custom event that components can listen for
    const event = new CustomEvent('pipeline-update', { 
      detail: { 
        pipelineId: this.pipelineId,
        timestamp: Date.now(),
        type: 'step-progress-update' 
      } 
    });
    window.dispatchEvent(event);
  }
  
  /**
   * Fetch current pipeline status from the API
   */
  async fetchPipelineStatus(): Promise<Partial<PipelineData>> {
    try {
      const data = await api.agent.getPipelineStatus(this.pipelineId);
      this.updatePipelineData(data);
      return data;
    } catch (error) {
      console.error('Error fetching pipeline status:', error);
      return this.pipelineData;
    }
  }
}

// Create a hook to use the StepProgressManager in React components
export function useStepProgressManager(
  pipelineId: string,
  availableSteps: string[] = []
): StepProgressManager {
  const [manager] = useState(
    () => new StepProgressManager(pipelineId, availableSteps)
  );
  
  useEffect(() => {
    // Update pipeline ID if it changes
    if (pipelineId !== manager.getPipelineId()) {
      manager.setPipelineId(pipelineId);
    }
    
    // Set available steps if they change
    if (availableSteps.length > 0) {
      manager.setAvailableSteps(availableSteps);
    }
    
    // Setup WebSocket listeners for real-time updates
    if (pipelineId) {
      const socket = getSocket();
      
      const onStepStarted = (data: any) => {
        if (data.pipeline_id === pipelineId) {
          manager.updateStepData(data.step, {
            status: 'running',
            message: 'Step execution started',
          });
        }
      };
      
      const onStepUpdated = (data: any) => {
        if (data.pipeline_id === pipelineId) {
          manager.updateStepData(data.step, {
            ...data.step_data,
            status: data.step_data.status || 'running',
          });
          
          manager.updatePipelineData({
            status: data.pipeline_status,
            completed_steps: data.completed_steps,
            total_steps: data.total_steps,
          });
        }
      };
      
      // Register WebSocket event handlers
      socket.on('step_started', onStepStarted);
      socket.on('step_updated', onStepUpdated);
      
      // Fetch initial pipeline data
      if (pipelineId) {
        manager.fetchPipelineStatus().catch(console.error);
      }
      
      // Cleanup function to remove event listeners
      return () => {
        socket.off('step_started', onStepStarted);
        socket.off('step_updated', onStepUpdated);
      };
    }
  }, [pipelineId, availableSteps, manager]);
  
  return manager;
}
