'use client';

import React, { createContext, useState, useContext, ReactNode, useRef, useEffect } from 'react';
import { Toast } from '@/components/Toast';

interface ToastItem {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ToastContextProps {
  addToast: (message: string, type: 'success' | 'error' | 'info') => void;
  removeToast: (id: string) => void;
  toastsEnabled: boolean;
  toggleToasts: () => void;
}

const ToastContext = createContext<ToastContextProps | undefined>(undefined);

let toastIdCounter = 0; // Add a counter for unique IDs

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [mounted, setMounted] = useState(false);
  const [toastsEnabled, setToastsEnabled] = useState(false); // Default is off
  const toastContainerRef = useRef<HTMLDivElement>(null);

  // Initialize from localStorage and set up event listener for changes
  useEffect(() => {
    setMounted(true);
    
    // Load toast preference from localStorage
    const storedPreference = localStorage.getItem('toastsEnabled');
    if (storedPreference !== null) {
      setToastsEnabled(storedPreference === 'true');
    }

    // Set up event listener for storage changes from other tabs/windows
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'toastsEnabled') {
        setToastsEnabled(e.newValue === 'true');
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  const addToast = (message: string, type: 'success' | 'error' | 'info') => {
    // Only add toast if they're enabled
    if (!toastsEnabled) return;
    
    const id = `toast-${toastIdCounter++}`; 
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const toggleToasts = () => {
    const newValue = !toastsEnabled;
    setToastsEnabled(newValue);
    localStorage.setItem('toastsEnabled', String(newValue));
  };

  return (
    <ToastContext.Provider value={{ addToast, removeToast, toastsEnabled, toggleToasts }}>
      {children}
      {mounted && toastsEnabled && (
        <div 
          ref={toastContainerRef}
          style={{
            position: 'fixed',
            top: '1rem',
            right: '1rem',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: '0.75rem',
            pointerEvents: 'none'
          }}
        >
          {toasts.map((toast) => (
            <div 
              key={toast.id} 
              style={{ pointerEvents: 'auto' }}
            >
              <Toast
                message={toast.message}
                type={toast.type}
                onClose={() => removeToast(toast.id)}
              />
            </div>
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
