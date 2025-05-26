interface AgentStatusProps {
  steps: Array<{
    id: string;
    status: string;
  }>;
  loading: boolean;
}

export function AgentStatus({ steps, loading }: AgentStatusProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 flex justify-center">
        <div className="text-gray-500">Loading agent status...</div>
      </div>
    );
  }

  const totalSteps = steps.length;
  const completedSteps = steps.filter(step => step.status === 'completed').length;
  const inProgressSteps = steps.filter(step => ['in_progress', 'waiting_input'].includes(step.status)).length;
  const pendingSteps = totalSteps - completedSteps - inProgressSteps;
  const progress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex flex-wrap items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Agent Status</h2>
        <span className="text-sm font-medium text-gray-500">
          {completedSteps} of {totalSteps} steps completed ({progress}%)
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
        <div 
          className="bg-primary-600 h-2.5 rounded-full transition-all duration-500" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{inProgressSteps}</div>
          <div className="text-sm text-gray-600">In Progress</div>
        </div>
        <div className="p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{completedSteps}</div>
          <div className="text-sm text-gray-600">Completed</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-600">{pendingSteps}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
      </div>
    </div>
  );
}
