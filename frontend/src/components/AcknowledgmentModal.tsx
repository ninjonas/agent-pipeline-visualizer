// Modal component for acknowledgment with comments
import { useState, useEffect, useRef } from 'react';

interface AcknowledgmentModalProps {
  isOpen: boolean;
  stepName: string;
  onClose: () => void;
  onAcknowledge: (comment: string) => Promise<void>;
  isLoading: boolean;
}

export default function AcknowledgmentModal({
  isOpen,
  stepName,
  onClose,
  onAcknowledge,
  isLoading
}: AcknowledgmentModalProps) {
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
  
  // Reset comment when modal opens
  useEffect(() => {
    if (isOpen) {
      setComment('');
    }
  }, [isOpen]);
  
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
        className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl"
      >
        <h3 className="text-xl font-bold mb-4 text-gray-900">
          Acknowledge Step
        </h3>
        
        <p className="mb-4 text-gray-800">
          You are about to acknowledge <span className="font-semibold">{formatStepName(stepName)}</span>. 
          The pipeline will continue execution after acknowledgment.
        </p>
        
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
              placeholder="Add any notes or comments about this acknowledgment (optional)"
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
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Acknowledging...
                </>
              ) : (
                <>
                  <span className="mr-1">✓</span>
                  Acknowledge and Continue
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
