// Modal component for batch acknowledgment of multiple steps
import { useState, useEffect, useRef } from 'react';

interface BatchAcknowledgmentModalProps {
  isOpen: boolean;
  steps: string[];
  onClose: () => void;
  onAcknowledge: (comment: string) => Promise<void>;
  isLoading: boolean;
}

export default function BatchAcknowledgmentModal({
  isOpen,
  steps,
  onClose,
  onAcknowledge,
  isLoading
}: BatchAcknowledgmentModalProps) {
  const [comment, setComment] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);
  
  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        if (!isLoading) {
          onClose();
        }
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose, isLoading]);
  
  // Handle escape key to close
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isLoading) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose, isLoading]);
  
  if (!isOpen) return null;
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onAcknowledge(comment);
  };
  
  // Format step name for display
  const formatStepName = (stepName: string): string => {
    return stepName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div 
        ref={modalRef}
        className="bg-white rounded-lg p-6 w-full max-w-lg shadow-xl"
      >
        <h3 className="text-xl font-bold mb-4 text-gray-900">
          Batch Acknowledge Steps
        </h3>
        
        <p className="mb-4 text-gray-800">
          You are about to acknowledge <span className="font-semibold">{steps.length} steps</span>. 
          The pipeline will continue execution after acknowledgment.
        </p>
        
        <div className="mb-4 bg-yellow-50 p-3 rounded-md border border-yellow-200">
          <h4 className="font-medium text-yellow-800 mb-2">Steps to acknowledge:</h4>
          <ul className="list-disc pl-5 space-y-1">
            {steps.map((stepName) => (
              <li key={stepName} className="text-gray-800">
                {formatStepName(stepName)}
              </li>
            ))}
          </ul>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">
              Optional Comment
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-2 text-gray-800"
              rows={3}
              placeholder="Add any notes or comments about this batch acknowledgment (optional)"
            />
          </div>
          
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Acknowledging...' : `Acknowledge ${steps.length} Steps`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
