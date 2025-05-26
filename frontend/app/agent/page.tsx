'use client';

import { useState, useEffect } from 'react';
import { StepCard } from '@/components/StepCard';
import { FileViewer } from '@/components/FileViewer';
import { AgentStatus } from '@/components/AgentStatus';
import { useAgentSteps } from '@/utils/hooks/useAgentSteps';
import { AGENT_STEPS, STEP_GROUPS } from '@/utils/constants';
import { Step } from '@/types/agent';

export default function AgentDashboard() {
  const { steps, loading, error, refreshSteps, updateStepOutput } = useAgentSteps();
  const [selectedStep, setSelectedStep] = useState<Step | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      refreshSteps();
    }, 5000);

    return () => clearInterval(interval);
  }, [refreshSteps]);

  const handleStepClick = (step: Step) => {
    setSelectedStep(step);
    setSelectedFile(null);
  };

  const handleFileSelect = (filePath: string) => {
    setSelectedFile(filePath);
  };

  const handleApproveStep = async (stepId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps/${stepId}/approve`, {
        method: 'POST',
      });
      
      if (response.ok) {
        refreshSteps();
      } else {
        console.error('Failed to approve step');
      }
    } catch (error) {
      console.error('Error approving step:', error);
    }
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6 text-primary-700">Agent Dashboard</h1>
      
      <AgentStatus steps={steps} loading={loading} />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-1 space-y-6">
          {STEP_GROUPS.map((group) => (
            <div key={group.id} className="bg-white rounded-lg shadow-sm p-4">
              <h2 className="text-xl font-semibold mb-3 text-primary-600">{group.name}</h2>
              <div className="space-y-3">
                {AGENT_STEPS.filter(step => step.group === group.id).map((step) => {
                  const stepData = steps.find(s => s.id === step.id);
                  return (
                    <StepCard
                      key={step.id}
                      step={{
                        id: step.id,
                        name: step.name,
                        description: step.description,
                        status: stepData?.status || 'pending',
                        requiresUserInput: step.requiresUserInput,
                        dependencies: step.dependencies,
                      }}
                      isSelected={selectedStep?.id === step.id}
                      onClick={handleStepClick}
                      onApprove={handleApproveStep}
                    />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
        
        <div className="lg:col-span-2">
          {selectedStep ? (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold text-primary-700">{selectedStep.name}</h2>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  selectedStep.status === 'completed' ? 'bg-green-100 text-green-800' :
                  selectedStep.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                  selectedStep.status === 'waiting_input' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {selectedStep.status.replace('_', ' ')}
                </span>
              </div>
              
              <p className="text-gray-600 mb-6">{selectedStep.description}</p>
              
              <FileViewer 
                stepId={selectedStep.id}
                selectedFile={selectedFile}
                onFileSelect={handleFileSelect}
                onSaveContent={updateStepOutput}
              />

              {selectedStep.requiresUserInput && selectedStep.status === 'waiting_input' && (
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => handleApproveStep(selectedStep.id)}
                    className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
                  >
                    Approve and Continue
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm p-6 flex items-center justify-center h-full">
              <p className="text-gray-500 text-lg">Select a step to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
