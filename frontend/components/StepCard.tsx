import { Step } from '@/types/agent';

interface StepCardProps {
  step: Step;
  isSelected: boolean;
  onClick: (step: Step) => void;
  onApprove: (stepId: string) => void;
  onRunStep?: (stepId: string) => void;
  isRunning?: boolean;
  completedSteps: string[];
  hasFilesForReview?: boolean; // Added to indicate if files are ready for review
}

export function StepCard({ step, isSelected, onClick, onApprove, onRunStep, isRunning = false, completedSteps = [], hasFilesForReview = false }: StepCardProps) {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-800',
    waiting_dependency: 'bg-purple-100 text-purple-800',
    in_progress: 'bg-blue-100 text-blue-800',
    waiting_input: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  
  const statusColor = statusColors[step.status as keyof typeof statusColors] || statusColors.pending;
  
  // Check if all dependencies are completed
  const canRun = step.dependencies.length === 0 || 
                step.dependencies.every(depId => completedSteps.includes(depId));
  
  // Determine if the approve button should be enabled
  const canApprove = step.status === 'waiting_input' && hasFilesForReview;
  
  return (
    <div 
      className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'border-primary-500 bg-primary-50' : 'border-gray-200 bg-white'
      }`}
      onClick={() => onClick(step)}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-medium text-gray-900">{step.name}</h3>
        <span className={`px-2 py-1 rounded-full text-xs ${statusColor}`}>
          {step.status.replace('_', ' ')}
        </span>
      </div>
      
      {step.requiresUserInput && (
        <div className="mt-2 text-xs text-gray-500 flex items-center">
          <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          Requires user review
        </div>
      )}
      
      {step.dependencies && step.dependencies.length > 0 && (
        <div className="mt-2 text-xs text-gray-500 flex items-center">
          <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
          Dependencies: {step.dependencies.join(', ')}
        </div>
      )}
      
      {step.status === 'waiting_input' && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            // Ensure onApprove is only called if the button is truly enabled,
            // though the disabled attribute should prevent this.
            if (canApprove) {
              onApprove(step.id);
            }
          }}
          disabled={!canApprove} // Disable button if not ready for approval
          className={`mt-3 w-full px-3 py-1.5 text-white text-xs rounded transition-colors ${
            canApprove ? 'bg-primary-600 hover:bg-primary-700' : 'bg-gray-300 text-gray-600 cursor-not-allowed'
          }`}
        >
          {hasFilesForReview ? 'Approve & Continue' : 'Waiting for Files'}
        </button>
      )}
      
      {(step.status === 'pending' || step.status === 'waiting_dependency' || step.status === 'failed') && onRunStep && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRunStep(step.id);
          }}
          disabled={isRunning || !canRun}
          className={`mt-3 w-full px-3 py-1.5 text-xs rounded transition-colors ${
            isRunning 
              ? 'bg-gray-300 text-gray-600 cursor-not-allowed' 
              : canRun
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-600 cursor-not-allowed'
          }`}
        >
          {isRunning ? 'Running...' : canRun ? 'Run Step' : 'Waiting for Dependencies'}
        </button>
      )}
    </div>
  );
}
