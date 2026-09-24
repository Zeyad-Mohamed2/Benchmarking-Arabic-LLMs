import React from 'react';
import { Loader2 } from 'lucide-react';
import { ProgressState } from '../../types';

interface ProgressMonitorProps {
  isRunning: boolean;
  progress: ProgressState | null;
}

export const ProgressMonitor: React.FC<ProgressMonitorProps> = ({ isRunning, progress }) => {
  if (!isRunning) return null;

  if (!progress) {
    return (
      <div className="mb-8 max-w-4xl bg-[#111827] border border-gray-700/50 rounded-xl p-8 shadow-2xl flex items-center">
        <Loader2 className="animate-spin text-[#32C4B7] mr-4 h-8 w-8" />
        <h3 className="text-xl font-bold text-white">Connecting to server and initializing workflow...</h3>
      </div>
    );
  }

  const percentage = Math.round((progress.current / Math.max(progress.total, 1)) * 100);

  return (
    <div className="mb-8 w-full bg-[#111827] border border-gray-700/50 rounded-xl p-8 shadow-2xl">
      <h3 className="text-xl font-bold text-white mb-6 flex items-center">
        <Loader2 className="animate-spin text-[#32C4B7] mr-3 h-6 w-6" />
        🔄 Benchmark Progress
      </h3>

      <div className="w-full bg-gray-900 rounded-full h-3.5 border border-gray-800 p-0.5 relative mb-6">
        <div
          className="bg-[#32C4B7] h-full rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(50,196,183,0.4)]"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#1f2937] p-4 rounded-lg flex flex-col justify-center">
          <span className="text-xs text-gray-400 capitalize tracking-wider font-semibold mb-1">Current Stage</span>
          <span className="text-xl font-bold text-white">
            {progress.current < 20 ? '🔧 Initialization' : progress.current < 80 ? '⚙️ Processing' : '📊 Evaluation'}
          </span>
        </div>
        <div className="bg-[#1f2937] p-4 rounded-lg flex flex-col justify-center">
          <span className="text-xs text-gray-400 capitalize tracking-wider font-semibold mb-1">Progress</span>
          <span className="text-xl font-bold text-white">{percentage}%</span>
        </div>
        <div className="bg-[#1f2937] p-4 rounded-lg flex flex-col justify-center">
          <span className="text-xs text-gray-400 capitalize tracking-wider font-semibold mb-1">Status</span>
          <span className="text-sm font-medium text-[#32C4B7] truncate" title={progress.status}>
            {progress.status}
          </span>
        </div>
      </div>
    </div>
  );
};
