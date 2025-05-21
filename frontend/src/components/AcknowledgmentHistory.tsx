// Component to display acknowledgment history
import { useState } from 'react';
import { useAcknowledgmentHistory, AcknowledgmentRecord } from '@/lib/acknowledgmentHistory';

interface AcknowledgmentHistoryProps {
  pipelineId?: string;
  className?: string;
}

export default function AcknowledgmentHistory({ 
  pipelineId,
  className = ''
}: AcknowledgmentHistoryProps) {
  const { history, clearHistory } = useAcknowledgmentHistory(pipelineId);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  
  if (history.length === 0) {
    return null;
  }
  
  // Format date for display
  const formatDate = (timestamp: number): string => {
    return new Date(timestamp).toLocaleString();
  };
  
  // Get step name without prefix/suffix
  const formatStepName = (stepName: string): string => {
    // Convert snake_case to Title Case
    return stepName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  return (
    <div className={`mt-4 bg-white p-4 rounded-lg shadow ${className}`}>
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-gray-800">
          Acknowledgment History
          <span className="ml-2 text-sm text-gray-500">({history.length})</span>
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 text-sm hover:underline"
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </button>
          {history.length > 0 && (
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to clear the acknowledgment history?')) {
                  clearHistory();
                }
              }}
              className="text-red-600 text-sm hover:underline"
            >
              Clear
            </button>
          )}
        </div>
      </div>
      
      {isExpanded && (
        <div className="space-y-3 max-h-80 overflow-y-auto">
          {history.map((record: AcknowledgmentRecord, index: number) => (
            <div 
              key={`${record.stepName}-${record.timestamp}`}
              className="border-l-4 border-yellow-500 pl-3 py-2 bg-gray-50 rounded-r"
            >
              <div className="flex justify-between items-start">
                <div className="font-medium text-gray-800">
                  {formatStepName(record.stepName)}
                </div>
                <div className="text-xs text-gray-500">
                  {formatDate(record.timestamp)}
                </div>
              </div>
              
              {record.comment && (
                <div className="mt-1 text-sm text-gray-700 bg-gray-100 p-2 rounded">
                  <span className="text-xs font-medium text-gray-500">Comment:</span> {record.comment}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {!isExpanded && history.length > 0 && (
        <div className="text-sm text-gray-600">
          {history.length} acknowledgments recorded. Click "Expand" to view.
        </div>
      )}
    </div>
  );
}
