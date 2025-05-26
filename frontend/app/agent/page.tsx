'use client';

import { useState, useEffect, useCallback } from 'react'; // Added useCallback
import { StepCard } from '@/components/StepCard';
import { FileViewer } from '@/components/FileViewer';
import { AgentStatus } from '@/components/AgentStatus';
import { useAgentSteps } from '@/utils/hooks/useAgentSteps';
// import { AGENT_STEPS, STEP_GROUPS } from '@/utils/constants'; // Removed
import { Step, StepConfig, StepGroup } from '@/types/agent'; // Added StepConfig and StepGroup
import { useToast } from '@/contexts/ToastContext';

export default function AgentDashboard() {
  const { steps: agentStepsState, loading: agentStepsLoading, error: agentStepsError, refreshSteps, updateStepOutput, runStep, runningStep, optimisticallyUpdateStepStatus } = useAgentSteps();
  const [selectedStep, setSelectedStep] = useState<Step | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [filesForSelectedStep, setFilesForSelectedStep] = useState<string[]>([]);
  const { addToast } = useToast();

  const [agentConfig, setAgentConfig] = useState<StepConfig[]>([]);
  const [stepGroups, setStepGroups] = useState<StepGroup[]>([]);
  const [configLoading, setConfigLoading] = useState(true);

  const fetchAgentConfig = useCallback(async () => {
    setConfigLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/config`);
      if (!response.ok) {
        throw new Error(`Failed to fetch agent configuration: ${response.status}`);
      }
      const data = await response.json();
      setAgentConfig(data.steps || []); // Assuming config.json has a "steps" array

      // Derive STEP_GROUPS from the fetched config
      const uniqueGroups: { [key: string]: string } = {};
      (data.steps || []).forEach((step: StepConfig) => {
        if (step.group) {
          // Create a more descriptive name if needed, or use a predefined map
          const groupName = step.group.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          uniqueGroups[step.group] = groupName;
        }
      });
      const derivedStepGroups = Object.entries(uniqueGroups).map(([id, name]) => ({ id, name }));
      setStepGroups(derivedStepGroups);

    } catch (error: any) {
      addToast(`Error fetching agent config: ${error.message}`, 'error');
      console.error("Error fetching agent config:", error);
      setAgentConfig([]); // Set to empty array on error
      setStepGroups([]);
    } finally {
      setConfigLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchAgentConfig();
  }, [fetchAgentConfig]);


  useEffect(() => {
    const interval = setInterval(() => {
      refreshSteps(); // This comes from useAgentSteps hook
    }, 5000);

    return () => clearInterval(interval);
  }, [refreshSteps]);

  const handleStepClick = (step: Step) => { // Step type here is the enriched Step from useAgentSteps
    setSelectedStep(step);
    setSelectedFile(null);
  };

  const handleFileSelect = (filePath: string) => {
    setSelectedFile(filePath);
  };

  const handleFilesLoaded = (loadedFiles: string[]) => {
    setFilesForSelectedStep(loadedFiles);
  };

  const handleApproveStep = async (stepId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000'}/api/steps/${stepId}/approve`, {
        method: 'POST',
      });

      const stepConfigForToast = agentConfig.find(s => s.id === stepId);
      const stepNameForToast = stepConfigForToast?.name || stepId;

      if (response.ok) {
        addToast(`Step "${stepNameForToast}" approval signaled. Waiting for agent confirmation...`, 'info');

        let currentStepsState = agentStepsState; // Start with current known steps from useAgentSteps
        let approvedStepIsConfirmedCompleted = false;
        let attempts = 0;
        const maxAttempts = 10; 
        const pollInterval = 500; 

        while (!approvedStepIsConfirmedCompleted && attempts < maxAttempts) {
          currentStepsState = await refreshSteps(); 
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
          addToast(`Step "${stepNameForToast}" did not confirm completion quickly. Auto-run of next steps might rely on next scheduled refresh.`, 'info');
        }
        
        for (const potentialNextStepConfig of agentConfig) { // Use fetched agentConfig
          const potentialNextStepData = currentStepsState.find(s => s.id === potentialNextStepConfig.id);

          if (potentialNextStepData && (potentialNextStepData.status === 'pending' || potentialNextStepData.status === 'waiting_dependency')) {
            const dependenciesMet = potentialNextStepConfig.dependencies.every(depId => {
              const depStepData = currentStepsState.find(s => s.id === depId);
              return depStepData && depStepData.status === 'completed';
            });

            if (dependenciesMet && !potentialNextStepData.requiresUserInput) {
              addToast(`Dependencies met for "${potentialNextStepConfig.name}", attempting to run.`, 'info');
              const runResult = await handleRunStep(potentialNextStepConfig.id);
              currentStepsState = runResult.updatedSteps; 
            } else if (dependenciesMet && potentialNextStepData.requiresUserInput) {
              addToast(`Dependencies met for "${potentialNextStepConfig.name}", but it requires user input.`, 'info');
            }
          }
        }

        const currentApprovedStepIndex = agentConfig.findIndex(s => s.id === stepId);
        if (currentApprovedStepIndex >= 0) {
          let nextStepToSelect: Step | null = null; // Type should be Step
          for (let i = 0; i < agentConfig.length; i++) {
            const config = agentConfig[i];
            const data = currentStepsState.find(s => s.id === config.id);
            if (data && data.status !== 'completed' && 
                (data.status === 'waiting_input' || data.status === 'in_progress' || data.status === 'pending' || data.status === 'failed')) {
              // Construct the full Step object for selection
              nextStepToSelect = {
                id: data.id,
                name: config.name,
                description: config.description,
                status: data.status,
                requiresUserInput: config.requiresUserInput,
                dependencies: config.dependencies,
                group: config.group,
                message: data.message 
              };
              break; 
            }
          }
          if (nextStepToSelect) {
            setSelectedStep(nextStepToSelect);
            setSelectedFile(null); 
          } else {
            addToast('All steps are completed or no further actions pending.', 'success');
            setSelectedStep(null); 
          }
        }

      } else {
        const errorText = await response.text();
        addToast(`Failed to approve step "${stepNameForToast}": ${response.status} ${errorText}`, 'error');
        console.error('Failed to approve step:', errorText);
      }
    } catch (error: any) {
      const stepConfigForToast = agentConfig.find(s => s.id === stepId);
      const stepName = stepConfigForToast?.name || stepId;
      console.error(`Error approving step "${stepName}":`, error);
      addToast(`Error approving step "${stepName}": ${error.message}`, 'error');
    }
  };

  const handleRunStep = async (stepId: string): Promise<{ success: boolean, updatedSteps: Step[] }> => {
    const result = await runStep(stepId); 
    
    const stepConfig = agentConfig.find(s => s.id === stepId);
    const stepData = result.updatedSteps.find(s => s.id === stepId);

    if (selectedStep?.id === stepId && stepConfig && stepData) {
        setSelectedStep({
            id: stepData.id,
            name: stepConfig.name,
            description: stepConfig.description,
            status: stepData.status,
            requiresUserInput: stepConfig.requiresUserInput,
            dependencies: stepConfig.dependencies,
            group: stepConfig.group,
            message: stepData.message
        });
        setSelectedFile(null); 
    } else if (stepData && stepData.status === 'waiting_input' && !selectedStep && stepConfig) {
         setSelectedStep({
            id: stepData.id,
            name: stepConfig.name,
            description: stepConfig.description,
            status: stepData.status,
            requiresUserInput: stepConfig.requiresUserInput,
            dependencies: stepConfig.dependencies,
            group: stepConfig.group,
            message: stepData.message
        });
        setSelectedFile(null);
    }
    
    return result;
  };

  if (configLoading || agentStepsLoading) { // Combined loading state
    return <div className="container mx-auto py-6 text-center">Loading configuration and agent state...</div>;
  }

  if (agentStepsError) { // Display error from useAgentSteps if any
    return <div className="container mx-auto py-6 text-center text-red-500">Error loading agent state: {agentStepsError}</div>;
  }
  
  // Ensure agentConfig is not empty before rendering dependent UI
  if (!agentConfig.length && !configLoading) {
    return <div className="container mx-auto py-6 text-center text-red-500">Failed to load agent configuration. Please check the console or try again.</div>;
  }

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6 text-primary-700">Agent Dashboard</h1>
      
      <AgentStatus steps={agentStepsState} loading={agentStepsLoading} /> 
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-1 space-y-6 overflow-y-auto max-h-[calc(100vh-12rem)]">
          {stepGroups.map((group) => ( // Use derived stepGroups
            <div key={group.id} className="bg-white rounded-lg shadow-sm p-4">
              <h2 className="text-xl font-semibold mb-3 text-primary-600">{group.name}</h2>
              <div className="space-y-3">
                {agentConfig.filter(step => step.group === group.id).map((stepCfg) => { // Iterate over agentConfig
                  const stepData = agentStepsState.find(s => s.id === stepCfg.id); // Find matching state
                  // Construct the Step object for StepCard
                  const cardStep: Step = {
                    id: stepCfg.id,
                    name: stepCfg.name,
                    description: stepCfg.description,
                    status: stepData?.status || 'pending',
                    requiresUserInput: stepCfg.requiresUserInput,
                    dependencies: stepCfg.dependencies,
                    group: stepCfg.group,
                    message: stepData?.message 
                  };
                  return (
                    <StepCard
                      key={cardStep.id}
                      step={cardStep}
                      isSelected={selectedStep?.id === cardStep.id}
                      onClick={() => handleStepClick(cardStep)} // Pass the full Step object
                      onApprove={handleApproveStep}
                      onRunStep={handleRunStep}
                      isRunning={runningStep === cardStep.id}
                      completedSteps={agentStepsState.filter(s => s.status === 'completed').map(s => s.id)}
                      hasFilesForReview={selectedStep?.id === cardStep.id && filesForSelectedStep.length > 0} 
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
                onFilesLoaded={handleFilesLoaded} 
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
                  {(() => {
                    const completedStepIds = agentStepsState.filter(s => s.status === 'completed').map(s => s.id);
                    // Ensure selectedStep.dependencies is not undefined
                    const dependencies = selectedStep.dependencies || [];
                    const canRun = dependencies.length === 0 || 
                                  dependencies.every(depId => completedStepIds.includes(depId));
                    
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
