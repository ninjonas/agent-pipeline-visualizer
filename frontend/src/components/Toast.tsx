// Toast notification component for showing success/error messages
import { useState, useEffect } from 'react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastProps {
  message: ToastMessage;
  onClose: (id: number) => void;
}

const Toast = ({ message, onClose }: ToastProps) => {
  useEffect(() => {
    // Auto-dismiss toast after 5 seconds
    const timer = setTimeout(() => {
      onClose(message.id);
    }, 5000);

    return () => clearTimeout(timer);
  }, [message.id, onClose]);

  const getToastStyles = (): string => {
    switch (message.type) {
      case 'success':
        return 'bg-green-100 border-green-500 text-green-800';
      case 'error':
        return 'bg-red-100 border-red-500 text-red-800';
      case 'warning':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'info':
        return 'bg-blue-100 border-blue-500 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-500 text-gray-800';
    }
  };

  const getToastIcon = (): string => {
    switch (message.type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      case 'info':
        return 'ℹ';
      default:
        return '•';
    }
  };

  return (
    <div className={`${getToastStyles()} p-4 rounded-md shadow-md border-l-4 flex justify-between items-center mb-2 animate-slideInRight`}>
      <div className="flex items-center">
        <span className="mr-2 font-bold">{getToastIcon()}</span>
        <span>{message.message}</span>
      </div>
      <button 
        onClick={() => onClose(message.id)} 
        className="ml-4 text-lg font-medium opacity-70 hover:opacity-100"
      >
        ×
      </button>
    </div>
  );
};

export const ToastContainer = ({ 
  messages, 
  onClose 
}: { 
  messages: ToastMessage[], 
  onClose: (id: number) => void 
}) => {
  return (
    <div className="fixed top-4 right-4 z-50 max-w-md w-full">
      {messages.map((message) => (
        <Toast key={message.id} message={message} onClose={onClose} />
      ))}
    </div>
  );
};

// Hook for managing toast notifications
export const useToast = () => {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const addMessage = (type: ToastType, message: string) => {
    const id = Date.now();
    setMessages((prev) => [...prev, { id, type, message }]);
    return id;
  };

  const removeMessage = (id: number) => {
    setMessages((prev) => prev.filter((message) => message.id !== id));
  };

  return {
    messages,
    addSuccess: (message: string) => addMessage('success', message),
    addError: (message: string) => addMessage('error', message),
    addWarning: (message: string) => addMessage('warning', message),
    addInfo: (message: string) => addMessage('info', message),
    removeMessage
  };
};
