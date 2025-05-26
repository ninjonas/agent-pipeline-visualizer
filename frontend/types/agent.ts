export interface Step {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'waiting_input' | 'waiting_dependency';
  requiresUserInput: boolean;
  dependencies: string[];
  group?: string; // Optional: Group the step belongs to
  message?: string; // Optional: Any message associated with the current status
  // Add other relevant fields from your config if needed
}

// Definition for the static configuration of a step (from config.json)
export interface StepConfig {
  id: string;
  name: string;
  description: string;
  requiresUserInput: boolean;
  dependencies: string[];
  group: string; // Group is mandatory in config
}

// Definition for a step group
export interface StepGroup {
  id: string;
  name: string;
}
