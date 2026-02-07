'use client';

import { ResearchStatus } from '@/lib/api';

interface ProgressTrackerProps {
  status: ResearchStatus | null;
}

export default function ProgressTracker({ status }: ProgressTrackerProps) {
  if (!status) return null;

  const stageLabels: Record<string, string> = {
    planning: 'Planning Research Strategy',
    executing: 'Gathering Information',
    quality_check: 'Validating Quality',
    synthesizing: 'Creating Report',
    completed: 'Complete',
    failed: 'Failed',
  };

  const stageLabel = stageLabels[status.current_stage] || status.current_stage;

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-800">
            {stageLabel}
          </h3>
          <span className="text-sm text-gray-600">
            {status.progress}%
          </span>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${status.progress}%` }}
          />
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Sources Collected:</span> {status.sources_collected}
          </div>
          <div>
            <span className="font-medium">Iteration:</span> {status.iteration}
          </div>
        </div>

        {status.error_message && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
            Error: {status.error_message}
          </div>
        )}
      </div>
    </div>
  );
}
