'use client';

import { useToast } from '@/contexts/ToastContext';

export function ToastToggle() {
  const { toastsEnabled, toggleToasts } = useToast();

  return (
    <div className="flex items-center">
      <span className="text-sm mr-2 text-gray-600">Toast</span>
      <button
        type="button"
        onClick={toggleToasts}
        className={`relative inline-flex h-6 w-11 items-center rounded-full ${
          toastsEnabled ? 'bg-primary-600' : 'bg-gray-300'
        } transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:ring-offset-2`}
        role="switch"
        aria-checked={toastsEnabled}
      >
        <span
          className={`${
            toastsEnabled ? 'translate-x-6' : 'translate-x-1'
          } inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300`}
        />
      </button>
    </div>
  );
}
