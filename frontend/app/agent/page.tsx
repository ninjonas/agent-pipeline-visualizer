'use client';

import { useState, useEffect } from 'react';
import { StepCard } from '@/components/StepCard';
import { FileViewer } from '@/components/FileViewer';
import { AgentStatus } from '@/components/AgentStatus';
import { useAgentSteps } from '@/utils/hooks/useAgentSteps';
import { AGENT_STEPS, STEP_GROUPS } from '@/utils/constants';
import { Step } from '@/types/agent';
import { useToast } from '@/contexts/ToastContext';

export default function AgentDashboard() {
  const { steps, loading, error, refreshSteps, updateStepOutput, runStep, runningStep, optimisticallyUpdateStepStatus } = useAgentSteps();
  const [selectedStep, setSelectedStep] = useState<Step | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [filesForSelectedStep, setFilesForSelectedStep] = useState<string[]>([]); // New state for files
  const { addToast } = useToast();

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

  const handleFilesLoaded = (loadedFiles: string[]) => { // Handler for when files are loaded by FileViewer
    setFilesForSelectedStep(loadedFiles);
  };

  const handleApproveStep = async (stepId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps/${stepId}/approve`, {
        method: 'POST',
      });

      if (response.ok) {
        const stepConfigForToast = AGENT_STEPS.find(s => s.id === stepId);
        const stepNameForToast = stepConfigForToast?.name || stepId;
        addToast(`Step "${stepNameForToast}" approval signaled. Waiting for agent confirmation...`, 'info');

        let currentStepsState = steps; // Start with current known steps
        let approvedStepIsConfirmedCompleted = false;
        let attempts = 0;
        const maxAttempts = 10; // Poll for up to 5 seconds (10 * 500ms)
        const pollInterval = 500; 

        while (!approvedStepIsConfirmedCompleted && attempts < maxAttempts) {
          currentStepsState = await refreshSteps(); // Get the latest state from backend
          const approvedStepData = currentStepsState.find(s => s.id === stepId);
          if (approvedStepData && approvedStepData.status === 'completed') {
            approvedStepIsConfirmedCompleted = true;
            addToast(`Step "${stepNameForToast}" confirmed completed by agent.`, 'success');
          } else {
            attempts++;
            await new Promise(resolve => setTimeout(resolve, pollInterval));
          }
        }

        if (!approvedStepIsConfirmedCompleted) {
          addToast(`Step "${stepNameForToast}" did not confirm completion quickly. Auto-run of next steps might rely on next scheduled refresh.`, 'info'); // Changed 'warning' to 'info'
          // Proceed with currentStepsState, which might not have the approved step as 'completed' yet.
          // The regular polling or a manual refresh will eventually catch up.
        }
        
        // Ensure stepConfig (for dependencies) is from the constant AGENT_STEPS
        // and stepData (for status and requiresUserInput) is from currentStepsState (from backend)
        for (const potentialNextStepConfig of AGENT_STEPS) {
          const potentialNextStepData = currentStepsState.find(s => s.id === potentialNextStepConfig.id);

          if (potentialNextStepData && (potentialNextStepData.status === 'pending' || potentialNextStepData.status === 'waiting_dependency')) {
            const dependenciesMet = potentialNextStepConfig.dependencies.every(depId => {
              const depStepData = currentStepsState.find(s => s.id === depId);
              return depStepData && depStepData.status === 'completed';
            });

            if (dependenciesMet && !potentialNextStepData.requiresUserInput) {
              addToast(`Dependencies met for "${potentialNextStepConfig.name}", attempting to run.`, 'info');
              // runStep is already awaited in handleRunStep, and handleRunStep returns a promise
              const runResult = await handleRunStep(potentialNextStepConfig.id);
              currentStepsState = runResult.updatedSteps; // Refresh currentStepsState for the loop
            } else if (dependenciesMet && potentialNextStepData.requiresUserInput) {
              addToast(`Dependencies met for "${potentialNextStepConfig.name}", but it requires user input.`, 'info');
            }
          }
        }

        // UI update logic for selecting next step to focus on
        const currentApprovedStepIndex = AGENT_STEPS.findIndex(s => s.id === stepId);
        if (currentApprovedStepIndex >= 0) {
          let nextStepToSelect = null;
          // Try to find the next step that is not yet completed and is actionable
          for (let i = 0; i < AGENT_STEPS.length; i++) {
            const config = AGENT_STEPS[i];
            const data = currentStepsState.find(s => s.id === config.id);
            if (data && data.status !== 'completed' && 
                (data.status === 'waiting_input' || data.status === 'in_progress' || data.status === 'pending' || data.status === 'failed')) {
              nextStepToSelect = {
                ...data, // Use the latest data from currentStepsState
                name: config.name,
                description: config.description,
                requiresUserInput: config.requiresUserInput,
                dependencies: config.dependencies,
              };
              break; 
            }
          }
          if (nextStepToSelect) {
            setSelectedStep(nextStepToSelect);
            setSelectedFile(null); // Reset file view when step selection changes
          } else {
            addToast('All steps are completed or no further actions pending.', 'success');
            setSelectedStep(null); 
          }
        }

      } else {
        const errorText = await response.text();
        const stepName = AGENT_STEPS.find(s => s.id === stepId)?.name || stepId;
        addToast(`Failed to approve step "${stepName}": ${response.status} ${errorText}`, 'error');
        console.error('Failed to approve step:', errorText);
      }
    } catch (error: any) {
      const stepName = AGENT_STEPS.find(s => s.id === stepId)?.name || stepId;
      console.error(`Error approving step "${stepName}":`, error);
      addToast(`Error approving step "${stepName}": ${error.message}`, 'error');
    }
  };

  const handleRunStep = async (stepId: string): Promise<{ success: boolean, updatedSteps: Step[] }> => {
    // Most toasting is now handled by the runStep hook.
    const result = await runStep(stepId); 
    
    // Update the selected step details if it's the one that was run
    const stepConfig = AGENT_STEPS.find(s => s.id === stepId);
    const stepData = result.updatedSteps.find(s => s.id === stepId);

    if (selectedStep?.id === stepId && stepConfig && stepData) {
        setSelectedStep({
            ...stepData,
            name: stepConfig.name,
            description: stepConfig.description,
            requiresUserInput: stepConfig.requiresUserInput,
            dependencies: stepConfig.dependencies,
        });
        setSelectedFile(null); // Reset file view as step state changed
    } else if (stepData && stepData.status === 'waiting_input' && !selectedStep) {
        // If no step is selected, and a step just went to waiting_input, select it.
         setSelectedStep({
            ...stepData,
            name: stepConfig?.name || stepId,
            description: stepConfig?.description || '',
            requiresUserInput: stepConfig?.requiresUserInput || false,
            dependencies: stepConfig?.dependencies || [],
        });
        setSelectedFile(null);
    }
    
    return result;
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
                      onRunStep={handleRunStep}
                      isRunning={runningStep === step.id}
                      completedSteps={steps.filter(s => s.status === 'completed').map(s => s.id)}
                      hasFilesForReview={selectedStep?.id === step.id && filesForSelectedStep.length > 0} // Pass hasFilesForReview
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
                onFilesLoaded={handleFilesLoaded} // Pass the handler to FileViewer
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
              
              {(selectedStep.status === 'pending' || selectedStep.status === 'waiting_dependency' || selectedStep.status === 'failed') && (
                <div className="mt-6 flex justify-end">
                  {/* Check if all dependencies are completed */}
                  {(() => {
                    const completedStepIds = steps.filter(s => s.status === 'completed').map(s => s.id);
                    const canRun = selectedStep.dependencies.length === 0 || 
                                  selectedStep.dependencies.every(depId => completedStepIds.includes(depId));
                    
                    return (
                      <button
                        onClick={() => handleRunStep(selectedStep.id)}
                        disabled={runningStep === selectedStep.id || !canRun}
                        className={`px-4 py-2 rounded-md transition-colors ${
                          runningStep === selectedStep.id 
                            ? 'bg-gray-300 text-gray-600 cursor-not-allowed' 
                            : canRun
                              ? 'bg-blue-600 text-white hover:bg-blue-700'
                              : 'bg-gray-300 text-gray-600 cursor-not-allowed'
                        }`}
                      >
                        {runningStep === selectedStep.id ? 'Running...' : canRun ? 'Run Step' : 'Waiting for Dependencies'}
                      </button>
                    );
                  })()}
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
