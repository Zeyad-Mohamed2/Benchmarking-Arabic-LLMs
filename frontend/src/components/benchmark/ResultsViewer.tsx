import React, { useState } from 'react';
import { Download, BarChart2, Database, CheckCircle2, XCircle, Trophy } from 'lucide-react';
import { BenchmarkResults, TaskType } from '../../types';
import { ModelRadarChart } from '../charts/ModelRadarChart';
import { promoteToLeaderboard } from '../../services/api';

interface ResultsViewerProps {
  results: BenchmarkResults;
  task: TaskType;
  apiBase: string;
}

export const ResultsViewer: React.FC<ResultsViewerProps> = ({ results, task, apiBase }) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'radar' | 'llm' | 'scores' | 'stats'>('summary');
  const [promotionStatus, setPromotionStatus] = useState<Record<string, string>>({});
  const [isPromoting, setIsPromoting] = useState<string | null>(null);

  const handlePromote = async (modelName: string) => {
    const modelData = results.model_results[modelName];
    if (!modelData || !modelData.scores) return;

    setIsPromoting(modelName);
    try {
      const res = await promoteToLeaderboard(task, modelName, modelData.scores);
      if (res.success) {
        setPromotionStatus(prev => ({ ...prev, [modelName]: 'success' }));
      } else {
        setPromotionStatus(prev => ({ ...prev, [modelName]: `error: ${res.error || 'Failed'}` }));
      }
    } catch (err: any) {
      setPromotionStatus(prev => ({ ...prev, [modelName]: `error: ${err.message}` }));
    } finally {
      setIsPromoting(null);
    }
  };

  return (
    <div className="bg-[#111827] border border-gray-700/50 rounded-xl shadow-2xl overflow-hidden max-w-6xl mb-8">
      {/* Download & Promotion Bar */}
      <div className="p-6 border-b border-gray-700/50 bg-[#1f2937]/30 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-white mb-1 flex items-center">
            <Download className="h-5 w-5 mr-2 text-[#32C4B7]" /> Benchmark Exports
          </h3>
          <p className="text-xs text-gray-400">Download formatted Excel workbooks or promote models directly into the public leaderboard.</p>
        </div>

        <div className="flex flex-wrap gap-3">
          {results.comparison_excel_path && (
            <button
              onClick={() =>
                window.open(`${apiBase}/download?file_path=${encodeURIComponent(results.comparison_excel_path!)}`, '_blank')
              }
              className="px-4 py-2 bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19] font-semibold rounded shadow transition-colors flex items-center text-sm"
            >
              <BarChart2 className="h-4 w-4 mr-2" /> Download Comparison
            </button>
          )}
          {results.excel_path && !results.comparison_excel_path && (
            <button
              onClick={() =>
                window.open(`${apiBase}/download?file_path=${encodeURIComponent(results.excel_path!)}`, '_blank')
              }
              className="px-4 py-2 bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19] font-semibold rounded shadow transition-colors flex items-center text-sm"
            >
              <BarChart2 className="h-4 w-4 mr-2" /> Download Results
            </button>
          )}
          {results.detailed_samples_path && (
            <button
              onClick={() =>
                window.open(
                  `${apiBase}/download?file_path=${encodeURIComponent(results.detailed_samples_path!)}`,
                  '_blank'
                )
              }
              className="px-4 py-2 bg-[#374151] hover:bg-[#4b5563] text-gray-200 font-semibold rounded shadow transition-colors flex items-center text-sm"
            >
              <Database className="h-4 w-4 mr-2" /> Download Samples
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700/50 bg-[#0b0f19] overflow-x-auto">
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 whitespace-nowrap ${
            activeTab === 'summary'
              ? 'border-[#32C4B7] text-[#32C4B7]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          📊 Summary
        </button>
        <button
          onClick={() => setActiveTab('radar')}
          className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 whitespace-nowrap ${
            activeTab === 'radar'
              ? 'border-[#32C4B7] text-[#32C4B7]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          🕸️ Radar Analysis
        </button>
        {results?.stats?.semantic_matching_enabled && (
          <button
            onClick={() => setActiveTab('llm')}
            className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 whitespace-nowrap ${
              activeTab === 'llm'
                ? 'border-[#32C4B7] text-[#32C4B7]'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            🧠 LLM Analysis
          </button>
        )}
        <button
          onClick={() => setActiveTab('scores')}
          className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 whitespace-nowrap ${
            activeTab === 'scores'
              ? 'border-[#32C4B7] text-[#32C4B7]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          📈 Detailed Scores
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-6 py-3 text-sm font-semibold transition-colors border-b-2 whitespace-nowrap ${
            activeTab === 'stats'
              ? 'border-[#32C4B7] text-[#32C4B7]'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          📋 Statistics
        </button>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {/* SUMMARY TAB */}
        {activeTab === 'summary' && (
          <div>
            <h3 className="text-xl font-bold text-white mb-6">Benchmark Summary</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-400 uppercase bg-[#1f2937]/50 border-b border-gray-700">
                  <tr>
                    <th className="px-6 py-4 font-semibold tracking-wider">Model Configuration</th>
                    <th className="px-6 py-4 font-semibold tracking-wider">Total Examples</th>
                    <th className="px-6 py-4 font-semibold tracking-wider">Errors</th>
                    <th className="px-6 py-4 font-semibold tracking-wider">API Success</th>
                    <th className="px-6 py-4 font-semibold tracking-wider">Primary Score</th>
                    <th className="px-6 py-4 font-semibold tracking-wider text-right">Leaderboard</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {Object.entries(results.model_results).map(([model, metrics]) => {
                    const stats = metrics.stats || {};
                    const scores = metrics.scores || {};
                    const n_examples = stats.n_examples || 1;
                    const n_errors = stats.n_errors || 0;
                    const success_rate = ((n_examples - n_errors) / Math.max(n_examples, 1)) * 100;

                    let primaryScoreStr = 'N/A';
                    const acc = scores.Accuracy ?? scores.accuracy;
                    const r1 = scores.ROUGE1 ?? scores.rouge1;
                    const rl = scores.ROUGEL ?? scores.rougeL ?? scores.ROUGE ?? scores.rouge;
                    const em = scores.EM ?? scores.em;
                    const f1 = scores.F1 ?? scores.f1;

                    if (acc !== undefined && typeof acc === 'number') primaryScoreStr = `Accuracy: ${acc.toFixed(3)}`;
                    else if (r1 !== undefined && typeof r1 === 'number') primaryScoreStr = `ROUGE-1: ${r1.toFixed(3)}`;
                    else if (rl !== undefined && typeof rl === 'number') primaryScoreStr = `ROUGE-L: ${rl.toFixed(3)}`;
                    else if (em !== undefined && typeof em === 'number') primaryScoreStr = `EM: ${em.toFixed(3)}`;
                    else if (f1 !== undefined && typeof f1 === 'number') primaryScoreStr = `F1: ${f1.toFixed(3)}`;

                    const status = promotionStatus[model];

                    return (
                      <tr key={model} className="hover:bg-[#1f2937]/40 transition-colors">
                        <td className="px-6 py-4 font-semibold text-gray-200">
                          <div className="flex items-center">
                            <div className="w-2 h-2 rounded-full bg-[#32C4B7] mr-3"></div>
                            {model.replace(':free', '')}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-300 font-mono">{n_examples}</td>
                        <td className="px-6 py-4 text-gray-300 font-mono text-red-400">{n_errors}</td>
                        <td className="px-6 py-4 text-gray-300 font-mono">{success_rate.toFixed(1)}%</td>
                        <td className="px-6 py-4 text-[#32C4B7] font-mono font-semibold">{primaryScoreStr}</td>
                        <td className="px-6 py-4 text-right">
                          {status === 'success' ? (
                            <span className="inline-flex items-center text-xs font-semibold text-green-400 bg-green-900/30 border border-green-800/60 px-2.5 py-1 rounded">
                              <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Added
                            </span>
                          ) : (
                            <button
                              onClick={() => handlePromote(model)}
                              disabled={isPromoting === model}
                              className="inline-flex items-center text-xs font-medium text-[#32C4B7] hover:text-[#0b0f19] hover:bg-[#32C4B7] border border-[#32C4B7]/60 px-2.5 py-1 rounded transition-colors disabled:opacity-50"
                              title="Promote this model run to the leaderboard"
                            >
                              <Trophy className="w-3.5 h-3.5 mr-1" />
                              {isPromoting === model ? 'Adding...' : 'Add to Leaderboard'}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* RADAR TAB */}
        {activeTab === 'radar' && (
          <div>
            <ModelRadarChart results={results} />
          </div>
        )}

        {/* LLM ANALYSIS TAB */}
        {activeTab === 'llm' && (
          <div>
            <h3 className="text-xl font-bold text-white mb-6">Semantic Matching Analysis</h3>
            <div className="space-y-6">
              {Object.entries(results.model_results).map(([model, metrics]) => {
                const stats = metrics.stats || {};
                const avg_conf = stats.avg_semantic_confidence || 0;
                return (
                  <div key={model} className="bg-[#1f2937]/30 p-5 rounded border border-gray-700/50">
                    <h4 className="font-bold text-gray-200 mb-4">{model.replace(':free', '')}</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div className="bg-[#111827] p-3 rounded">
                        <div className="text-xs text-gray-500 mb-1">Semantic Matches</div>
                        <div className="text-lg font-bold text-white">{stats.semantic_matches || 0}</div>
                      </div>
                      <div className="bg-[#111827] p-3 rounded">
                        <div className="text-xs text-gray-500 mb-1">Semantic Match Rate</div>
                        <div className="text-lg font-bold text-white">
                          {((stats.semantic_match_rate || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="bg-[#111827] p-3 rounded">
                        <div className="text-xs text-gray-500 mb-1">Avg Confidence</div>
                        <div className="text-lg font-bold text-white">{avg_conf.toFixed(2)}</div>
                      </div>
                    </div>
                    {avg_conf >= 0.7 ? (
                      <div className="text-sm text-green-400 flex items-center">
                        <CheckCircle2 className="w-4 h-4 mr-2" /> High confidence - model outputs are semantically very
                        close
                      </div>
                    ) : avg_conf >= 0.4 ? (
                      <div className="text-sm text-yellow-400 flex items-center">
                        ⚠️ Moderate confidence - some outputs differ but convey similar meaning
                      </div>
                    ) : (
                      <div className="text-sm text-red-400 flex items-center">
                        <XCircle className="w-4 h-4 mr-2" /> Low confidence - significant semantic differences
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* DETAILED SCORES TAB */}
        {activeTab === 'scores' && (
          <div>
            <h3 className="text-xl font-bold text-white mb-6">Detailed Scores</h3>
            <div className="space-y-6">
              {Object.entries(results.model_results).map(([model, metrics]) => (
                <div key={model} className="bg-[#1f2937]/30 p-5 rounded border border-gray-700/50">
                  <h4 className="font-bold text-[#32C4B7] mb-4 text-lg">{model.replace(':free', '')}</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(metrics.scores || {}).map(([key, value]) => (
                      <div
                        key={key}
                        className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm flex flex-col justify-center transition-transform hover:scale-[1.02]"
                      >
                        <div
                          className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1 truncate"
                          title={key}
                        >
                          {key}
                        </div>
                        <div className="text-xl font-bold text-white">
                          {typeof value === 'number' ? value.toFixed(4) : String(value)}
                        </div>
                      </div>
                    ))}
                    {Object.keys(metrics.scores || {}).length === 0 && (
                      <div className="text-sm text-gray-500 col-span-full">No detailed scores available.</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* STATISTICS TAB */}
        {activeTab === 'stats' && (
          <div>
            <h3 className="text-xl font-bold text-white mb-6">Processing Statistics</h3>
            <div className="space-y-6">
              {Object.entries(results.model_results).map(([model, metrics]) => {
                const stats = metrics.stats || {};
                return (
                  <div key={model} className="bg-[#1f2937]/30 p-5 rounded border border-gray-700/50">
                    <h4 className="font-bold text-[#32C4B7] mb-4 text-lg">{model.replace(':free', '')}</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                        <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Total Examples
                        </div>
                        <div className="text-xl font-bold text-white">{stats.n_examples || 0}</div>
                      </div>
                      <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                        <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Successful
                        </div>
                        <div className="text-xl font-bold text-green-400">
                          {stats.n_successful ?? ((stats.n_examples ?? 0) - (stats.n_errors ?? 0))}
                        </div>
                      </div>
                      <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                        <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Errors
                        </div>
                        <div className={`text-xl font-bold ${(stats.n_errors ?? 0) > 0 ? 'text-red-400' : 'text-gray-300'}`}>
                          {stats.n_errors ?? 0}
                        </div>
                      </div>
                      <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 shadow-sm transition-transform hover:scale-[1.02]">
                        <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1">
                          Success Rate
                        </div>
                        <div className="text-xl font-bold text-white">
                          {((stats.api_success_rate || 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    {Object.keys(stats).filter(
                      (k) =>
                        ![
                          'n_examples',
                          'n_successful',
                          'n_errors',
                          'api_success_rate',
                          'semantic_matches',
                          'semantic_match_rate',
                          'avg_semantic_confidence',
                          'semantic_matching_enabled',
                        ].includes(k)
                    ).length > 0 && (
                      <div className="mt-4 pt-4 border-t border-gray-700/50">
                        <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                          Other Information
                        </h5>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(stats)
                            .filter(
                              ([k]) =>
                                ![
                                  'n_examples',
                                  'n_successful',
                                  'n_errors',
                                  'api_success_rate',
                                  'semantic_matches',
                                  'semantic_match_rate',
                                  'avg_semantic_confidence',
                                  'semantic_matching_enabled',
                                ].includes(k)
                            )
                            .map(([key, value]) => (
                              <div key={key} className="bg-[#111827] p-3 rounded border border-gray-800 shadow-sm">
                                <div
                                  className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-1 truncate"
                                  title={key}
                                >
                                  {key.replace(/_/g, ' ')}
                                </div>
                                <div className="text-sm font-medium text-gray-300 truncate" title={String(value)}>
                                  {typeof value === 'number' && !Number.isInteger(value)
                                    ? value.toFixed(4)
                                    : String(value)}
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
