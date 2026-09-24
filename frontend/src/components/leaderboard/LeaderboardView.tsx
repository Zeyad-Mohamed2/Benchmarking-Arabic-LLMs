import React, { useState } from 'react';
import { Database, Loader2, XCircle } from 'lucide-react';
import { TaskType, LeaderboardEntry } from '../../types';

interface LeaderboardViewProps {
  leaderboardData: Record<string, LeaderboardEntry[]> | null;
  isLoading: boolean;
  error: string | null;
  activeTask: TaskType;
  setActiveTask: (t: TaskType) => void;
}

export const LeaderboardView: React.FC<LeaderboardViewProps> = ({
  leaderboardData,
  isLoading,
  error,
  activeTask,
  setActiveTask,
}) => {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  const currentRows = leaderboardData ? leaderboardData[activeTask] : null;

  const sortedRows = React.useMemo(() => {
    if (!currentRows) return [];
    if (!sortConfig) return currentRows;

    return [...currentRows].sort((a, b) => {
      const valA = a[sortConfig.key];
      const valB = b[sortConfig.key];
      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [currentRows, sortConfig]);

  const handleSort = (key: string) => {
    if (sortConfig?.key === key) {
      if (sortConfig.direction === 'desc') setSortConfig({ key, direction: 'asc' });
      else setSortConfig(null);
    } else {
      setSortConfig({ key, direction: 'desc' });
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Task selector tabs */}
      <div className="flex space-x-2 mb-8 border-b border-gray-800 pb-2">
        {(['question_answering', 'summarization', 'sarcasm'] as TaskType[]).map((t) => (
          <button
            key={t}
            onClick={() => {
              setActiveTask(t);
              setSortConfig(null);
            }}
            className={`px-5 py-2.5 text-sm font-bold rounded-t-lg transition-all ${
              activeTask === t
                ? 'bg-[#32C4B7] text-[#0b0f19] shadow-[0_-4px_10px_rgba(50,196,183,0.2)]'
                : 'text-gray-400 hover:text-gray-200 hover:bg-[#1f2937]'
            }`}
          >
            {t === 'question_answering'
              ? 'Question Answering'
              : t === 'summarization'
              ? 'Summarization'
              : 'Sarcasm Detection'}
          </button>
        ))}
      </div>

      {isLoading && (
        <div className="flex items-center justify-center p-20 text-gray-400">
          <Loader2 className="animate-spin mr-3 h-8 w-8 text-[#32C4B7]" />
          <span className="text-lg">Loading leaderboard data...</span>
        </div>
      )}

      {error && (
        <div className="text-red-400 bg-red-950/50 border border-red-900/50 p-6 rounded-xl flex items-center shadow-lg">
          <XCircle className="w-6 h-6 mr-3 shrink-0" />
          {error}
        </div>
      )}

      {!isLoading && currentRows && currentRows.length > 0 && (
        <div className="bg-[#111827] border border-gray-700/50 rounded-xl shadow-2xl overflow-hidden ring-1 ring-white/5">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse whitespace-nowrap">
              <thead>
                <tr className="bg-gradient-to-r from-[#1f2937]/80 to-[#111827] border-b border-gray-700/80">
                  <th className="p-5 font-bold text-[#32C4B7] text-sm uppercase tracking-wider sticky left-0 bg-[#1f2937] z-10 w-16 text-center">
                    Rank
                  </th>
                  {Object.keys(currentRows[0]).map((k, i) => (
                    <th
                      key={k}
                      className={`p-5 font-bold text-gray-300 text-xs uppercase tracking-wider cursor-pointer hover:bg-gray-700/50 transition-colors ${
                        i === 0 ? 'sticky left-16 bg-[#1f2937] z-10 shadow-[2px_0_5px_rgba(0,0,0,0.1)]' : ''
                      }`}
                      onClick={() => handleSort(k)}
                    >
                      <div className="flex items-center space-x-1">
                        <span>{k.replace(/_/g, ' ')}</span>
                        {sortConfig?.key === k && (
                          <span className="text-[#32C4B7] font-sans">
                            {sortConfig.direction === 'desc' ? '↓' : '↑'}
                          </span>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {sortedRows.map((row, idx) => {
                  const isTop1 = idx === 0;
                  const isTop2 = idx === 1;
                  const isTop3 = idx === 2;

                  let rankDisplay = `#${idx + 1}`;
                  let rankClass = 'text-gray-400 font-medium';
                  let rowClass = 'hover:bg-[#1f2937]/40 transition-colors duration-150';

                  if (isTop1) {
                    rankDisplay = '🥇 1';
                    rankClass = 'text-yellow-400 font-black text-lg drop-shadow-[0_0_8px_rgba(250,204,21,0.4)]';
                    rowClass += ' bg-gradient-to-r from-yellow-900/10 to-transparent';
                  } else if (isTop2) {
                    rankDisplay = '🥈 2';
                    rankClass = 'text-gray-300 font-bold text-lg drop-shadow-[0_0_8px_rgba(209,213,219,0.3)]';
                    rowClass += ' bg-gradient-to-r from-gray-700/10 to-transparent';
                  } else if (isTop3) {
                    rankDisplay = '🥉 3';
                    rankClass = 'text-amber-600 font-bold text-lg drop-shadow-[0_0_8px_rgba(217,119,6,0.3)]';
                    rowClass += ' bg-gradient-to-r from-amber-900/10 to-transparent';
                  }

                  return (
                    <tr key={idx} className={rowClass}>
                      <td
                        className={`p-4 text-center sticky left-0 ${
                          isTop1
                            ? 'bg-[#182132]'
                            : isTop2
                            ? 'bg-[#151d2c]'
                            : isTop3
                            ? 'bg-[#141b2a]'
                            : 'bg-[#111827]'
                        } group-hover:bg-[#1f2937]/40 z-10 ${rankClass}`}
                      >
                        {rankDisplay}
                      </td>
                      {Object.entries(row).map(([k, v], i) => (
                        <td
                          key={k}
                          className={`p-4 ${
                            i === 0
                              ? `font-semibold sticky left-16 z-10 shadow-[2px_0_5px_rgba(0,0,0,0.1)] ${
                                  isTop1
                                    ? 'text-yellow-400 bg-[#182132]'
                                    : isTop2
                                    ? 'text-gray-200 bg-[#151d2c]'
                                    : isTop3
                                    ? 'text-amber-500 bg-[#141b2a]'
                                    : 'text-[#32C4B7] bg-[#111827]'
                                }`
                              : 'text-gray-300 font-mono text-sm'
                          }`}
                        >
                          {typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(4) : String(v)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!isLoading && leaderboardData && (!currentRows || currentRows.length === 0) && (
        <div className="flex flex-col items-center justify-center p-20 bg-[#111827]/50 border border-gray-800 rounded-xl border-dashed">
          <Database className="w-12 h-12 text-gray-600 mb-4" />
          <p className="text-gray-400 text-lg">No leaderboard data found for {activeTask.replace(/_/g, ' ')}.</p>
          <p className="text-gray-500 text-sm mt-2">Run some benchmarks to generate results!</p>
        </div>
      )}
    </div>
  );
};
