'use client';

import { useState, useEffect } from 'react';
import { ConfigEditor } from '@/components/ConfigEditor';
import { AGENT_STEPS, STEP_GROUPS } from '@/utils/constants';
import { useToast } from '@/contexts/ToastContext';

export default function ConfigurationPage() {
  const [config, setConfig] = useState({
    steps: AGENT_STEPS
  });
  const [isLoading, setIsLoading] = useState(false);
  const { addToast } = useToast();

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/config`);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Error fetching config:', error);
      addToast('Failed to fetch configuration', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfig = async (updatedConfig: any) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedConfig),
      });
      
      if (response.ok) {
        addToast('Configuration saved successfully', 'success');
      } else {
        addToast('Failed to save configuration', 'error');
      }
    } catch (error) {
      console.error('Error saving config:', error);
      addToast('Error saving configuration', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6 text-primary-700">Agent Configuration</h1>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2 text-primary-600">Configure Agent Steps</h2>
          <p className="text-gray-600">
            Customize step dependencies, user input requirements, and the order of execution.
          </p>
        </div>
        
        <ConfigEditor 
          config={config} 
          stepGroups={STEP_GROUPS}
          isLoading={isLoading}
          onSave={saveConfig}
        />
      </div>
    </div>
  );
}
