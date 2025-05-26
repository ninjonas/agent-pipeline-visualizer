import { useEffect, useState } from 'react';

export interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
  duration?: number;
}

export function Toast({ message, type, onClose, duration = 3000 }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsExiting(true);
      setTimeout(onClose, 300); // Wait for exit animation to complete
    }, duration);

    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const bgColor = type === 'success' ? 'bg-green-100 text-green-800 border-green-300' :
                  type === 'error' ? 'bg-red-100 text-red-800 border-red-300' :
                  'bg-blue-100 text-blue-800 border-blue-300';

  const iconMap = {
    success: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
      </svg>
    ),
    error: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"></path>
      </svg>
    ),
    info: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd"></path>
      </svg>
    )
  };

  return (
    <div 
      style={{ 
        animation: isExiting ? 'fadeOutDown 0.3s ease-out' : 'fadeInUp 0.3s ease-out',
        maxWidth: '28rem', // max-w-md equivalent
        width: '100%'
      }}
    >
      <div className={`flex items-center p-4 rounded-lg border ${bgColor} shadow-lg`}>
        <div className="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 mr-3">
          {iconMap[type]}
        </div>
        <div className="ml-3 text-sm font-medium">{message}</div>
        <button 
          type="button" 
          className={`ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 inline-flex items-center justify-center h-8 w-8 ${
            type === 'success' ? 'hover:bg-green-200' : 
            type === 'error' ? 'hover:bg-red-200' : 
            'hover:bg-blue-200'
          }`}
          onClick={() => {
            setIsExiting(true);
            setTimeout(onClose, 300);
          }}
          aria-label="Close"
        >
          <span className="sr-only">Close</span>
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path>
          </svg>
        </button>
      </div>
    </div>
  );
}

export interface ToastContextProps {
  toasts: {
    id: string;
    message: string;
    type: 'success' | 'error' | 'info';
  }[];
  addToast: (message: string, type: 'success' | 'error' | 'info') => void;
  removeToast: (id: string) => void;
}
