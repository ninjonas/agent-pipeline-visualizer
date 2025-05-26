'use client';

import { useState } from 'react';

interface ConfigEditorProps {
  config: any;
  stepGroups: any[];
  isLoading: boolean;
  onSave: (config: any) => void;
}

export function ConfigEditor({ config, stepGroups, isLoading, onSave }: ConfigEditorProps) {
  const [editedConfig, setEditedConfig] = useState(config);
  
  const handleStepChange = (stepIndex: number, field: string, value: any) => {
    const updatedSteps = [...editedConfig.steps];
    updatedSteps[stepIndex] = { ...updatedSteps[stepIndex], [field]: value };
    setEditedConfig({ ...editedConfig, steps: updatedSteps });
  };
  
  const handleDependencyToggle = (stepIndex: number, dependencyId: string) => {
    const updatedSteps = [...editedConfig.steps];
    const currentDependencies = updatedSteps[stepIndex].dependencies || [];
    
    if (currentDependencies.includes(dependencyId)) {
      updatedSteps[stepIndex].dependencies = currentDependencies.filter(id => id !== dependencyId);
    } else {
      updatedSteps[stepIndex].dependencies = [...currentDependencies, dependencyId];
    }
    
    setEditedConfig({ ...editedConfig, steps: updatedSteps });
  };
  
  const saveConfig = () => {
    onSave(editedConfig);
  };
  
  return (
    <div>
      {stepGroups.map((group) => (
        <div key={group.id} className="mb-8">
          <h3 className="text-lg font-semibold mb-3 pb-2 border-b">{group.name}</h3>
          
          <div className="space-y-4">
            {editedConfig.steps
              .filter((step: any) => step.group === group.id)
              .map((step: any, index: number) => {
                const stepIndex = editedConfig.steps.findIndex((s: any) => s.id === step.id);
                
                return (
                  <div key={step.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex flex-wrap items-start justify-between mb-3">
                      <div>
                        <h4 className="font-medium">{step.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={step.requiresUserInput}
                            onChange={(e) => handleStepChange(stepIndex, 'requiresUserInput', e.target.checked)}
                            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-4 w-4"
                          />
                          <span className="ml-2 text-sm text-gray-700">Requires User Input</span>
                        </label>
                      </div>
                    </div>
                    
                    <div>
                      <h5 className="text-sm font-medium mb-2">Dependencies:</h5>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {editedConfig.steps
                          .filter((s: any) => s.id !== step.id)
                          .map((otherStep: any) => (
                            <label key={otherStep.id} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={(step.dependencies || []).includes(otherStep.id)}
                                onChange={() => handleDependencyToggle(stepIndex, otherStep.id)}
                                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-4 w-4"
                              />
                              <span className="ml-2 text-sm text-gray-700">{otherStep.name}</span>
                            </label>
                          ))}
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      ))}
      
      <div className="mt-6 flex justify-end">
        <button
          onClick={saveConfig}
          disabled={isLoading}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors disabled:bg-gray-400"
        >
          {isLoading ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
}
