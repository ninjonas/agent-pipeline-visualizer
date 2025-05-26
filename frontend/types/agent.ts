export interface Step {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'waiting_dependency' | 'in_progress' | 'waiting_input' | 'completed' | 'failed';
  requiresUserInput: boolean;
  dependencies: string[];
  group?: string;
  message?: string; // Added optional message field
}
