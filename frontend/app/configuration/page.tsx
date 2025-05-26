'use client';

import { useState, useEffect, useCallback } from 'react'; // Added useCallback
import { ConfigEditor } from '@/components/ConfigEditor';
// import { AGENT_STEPS, STEP_GROUPS } from '@/utils/constants'; // Removed
import { useToast } from '@/contexts/ToastContext';
import { StepConfig, StepGroup } from '@/types/agent'; // Import StepConfig and StepGroup

interface AgentConfigData {
  steps: StepConfig[];
  // Add other top-level config properties if any, e.g., status, as per your config.json structure
}

export default function ConfigurationPage() {
  // Initialize config with an empty steps array or a structure matching AgentConfigData
  const [config, setConfig] = useState<AgentConfigData>({ steps: [] });
  const [stepGroups, setStepGroups] = useState<StepGroup[]>([]); // State for derived step groups
  const [isLoading, setIsLoading] = useState(true); // Combined loading state for initial fetch
  const { addToast } = useToast();

  const fetchConfig = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/config`);
      if (!response.ok) {
        throw new Error(`Failed to fetch agent configuration: ${response.status}`);
      }
      const data: AgentConfigData = await response.json();
      setConfig(data); // Set the whole config object

      // Derive STEP_GROUPS from the fetched config
      const uniqueGroups: { [key: string]: string } = {};
      (data.steps || []).forEach((step) => {
        if (step.group) {
          const groupName = step.group.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          uniqueGroups[step.group] = groupName;
        }
      });
      const derivedStepGroups = Object.entries(uniqueGroups).map(([id, name]) => ({ id, name }));
      setStepGroups(derivedStepGroups);

    } catch (error: any) {
      console.error('Error fetching config:', error);
      addToast(`Failed to fetch configuration: ${error.message}`, 'error');
      setConfig({ steps: [] }); // Reset to default empty state on error
      setStepGroups([]);
    } finally {
      setIsLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const saveConfig = async (updatedConfig: AgentConfigData) => {
    setIsLoading(true); // This can be a different loading state, e.g., isSaving
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
        // Optionally re-fetch or update state if save changes structure significantly
        // For now, assume the saved config is immediately reflected or handled by ConfigEditor
        setConfig(updatedConfig); // Update local state with the saved config
        // Re-derive step groups if the groups could have changed
        const uniqueGroups: { [key: string]: string } = {};
        (updatedConfig.steps || []).forEach((step) => {
          if (step.group) {
            const groupName = step.group.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
            uniqueGroups[step.group] = groupName;
          }
        });
        const derivedStepGroups = Object.entries(uniqueGroups).map(([id, name]) => ({ id, name }));
        setStepGroups(derivedStepGroups);
      } else {
        const errorText = await response.text();
        addToast(`Failed to save configuration: ${response.status} ${errorText}`, 'error');
      }
    } catch (error: any) {
      console.error('Error saving config:', error);
      addToast(`Error saving configuration: ${error.message}`, 'error');
    } finally {
      setIsLoading(false); // Or setIsSaving(false)
    }
  };

  if (isLoading && config.steps.length === 0) { // Show loading only on initial fetch
    return <div className="container mx-auto py-6 text-center">Loading configuration...</div>;
  }

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
          config={config} // Pass the fetched and typed config
          stepGroups={stepGroups} // Pass the derived stepGroups
          isLoading={isLoading} // This could be a more specific isSaving state for the save operation
          onSave={saveConfig}
        />
      </div>
    </div>
  );
}
