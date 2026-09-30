import React, { useState } from 'react';
import { Settings, Play, Database, Key, Loader2, Minus, BrainCircuit, CheckCircle2, XCircle } from 'lucide-react';
import { TaskType, ProviderType, ModelSelection, ModelCatalogItem } from '../../types';
import { BrowseModelsModal } from '../modals/BrowseModelsModal';
import { DEFAULT_GEMINI_CATALOG } from '../../data/modelsCatalog';

interface ConfigSidebarProps {
  task: TaskType;
  setTask: (t: TaskType) => void;
  provider: ProviderType;
  setProvider: (p: ProviderType) => void;
  apiKey: string;
  setApiKey: (k: string) => void;
  models: ModelSelection[];
  setModels: React.Dispatch<React.SetStateAction<ModelSelection[]>>;
  numSamples: number;
  setNumSamples: (n: number) => void;
  datasetFile: File | null;
  setDatasetFile: (f: File | null) => void;
  useSemanticMatching: boolean;
  setUseSemanticMatching: (u: boolean) => void;
  geminiApiKey: string;
  setGeminiApiKey: (k: string) => void;
  geminiModel: string;
  setGeminiModel: (m: string) => void;
  enableCheckpointMode: boolean;
  setEnableCheckpointMode: (e: boolean) => void;
  checkpointInterval: number;
  setCheckpointInterval: (i: number) => void;
  isRunning: boolean;
  isTesting: boolean;
  testStatus: { success: boolean; messages: Record<string, string> } | null;
  onTestConnection: () => void;
  onRunBenchmark: () => void;
  openRouterModels: Record<string, string>;
  groqModels: Record<string, string>;
}

export const ConfigSidebar: React.FC<ConfigSidebarProps> = ({
  task,
  setTask,
  provider,
  setProvider,
  apiKey,
  setApiKey,
  models,
  setModels,
  numSamples,
  setNumSamples,
  datasetFile,
  setDatasetFile,
  useSemanticMatching,
  setUseSemanticMatching,
  geminiApiKey,
  setGeminiApiKey,
  geminiModel,
  setGeminiModel,
  enableCheckpointMode,
  setEnableCheckpointMode,
  checkpointInterval,
  setCheckpointInterval,
  isRunning,
  isTesting,
  testStatus,
  onTestConnection,
  onRunBenchmark,
  openRouterModels,
  groqModels,
}) => {
  const [isBrowseModalOpen, setIsBrowseModalOpen] = useState(false);
  const [isCustomGemini, setIsCustomGemini] = useState(false);
  const currentProviderModels = provider === 'groq' ? groqModels : openRouterModels;

  const handleApplyBrowseModels = (selected: ModelCatalogItem[]) => {
    setModels(
      selected.map((s) => ({
        display: s.name,
        custom: s.isCustom ? s.id : '',
        id: s.id,
      }))
    );
  };

  return (
    <aside className="w-80 bg-[#111827] border-r border-gray-800 p-6 flex flex-col shrink-0 overflow-y-auto relative z-10 custom-scrollbar scrollbar-thin">
      <h2 className="text-xl font-bold mb-6 text-white flex items-center tracking-tight">
        <Settings className="mr-2 h-5 w-5 text-[#32C4B7]" /> Configuration
      </h2>

      <div className="space-y-6">
        {/* Task Selection */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-400">Task Selection</label>
          <select
            className="w-full bg-[#1f2937] border border-gray-700 rounded-md p-2 text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
            value={task}
            onChange={(e) => setTask(e.target.value as TaskType)}
          >
            <option value="question_answering">Question Answering</option>
            <option value="summarization">Text Summarization</option>
            <option value="sarcasm">Sarcasm Detection</option>
          </select>
        </div>

        {/* Provider Switcher */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-400">Model Provider</label>
          <div className="flex bg-[#1f2937] rounded-md p-1 border border-gray-700">
            <button
              className={`flex-1 py-1.5 text-sm rounded transition-colors ${
                provider === 'openrouter' ? 'bg-[#374151] text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
              onClick={() => setProvider('openrouter')}
            >
              OpenRouter
            </button>
            <button
              className={`flex-1 py-1.5 text-sm rounded transition-colors ${
                provider === 'groq' ? 'bg-[#374151] text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
              onClick={() => setProvider('groq')}
            >
              Groq
            </button>
          </div>
        </div>

        {/* Model Selection via Browse Modal */}
        <div className="bg-[#1f2937]/30 border border-gray-700 p-4 rounded-lg space-y-3">
          <div className="flex justify-between items-center">
            <label className="text-sm font-medium text-gray-300 flex items-center">
              <Database className="mr-1.5 h-4 w-4 text-[#32C4B7]" /> Selected Models ({models.length}/3)
            </label>
          </div>

          {/* Selected Model Chips */}
          <div className="space-y-2">
            {models.map((m, idx) => {
              const displayName = m.display === 'Other (custom)' && m.custom ? m.custom : m.display;
              const isCustom = m.display === 'Other (custom)';
              return (
                <div
                  key={idx}
                  className="bg-[#111827] border border-gray-700/80 rounded-lg p-2.5 flex items-center justify-between text-xs group hover:border-[#32C4B7]/50 transition"
                >
                  <div className="min-w-0 flex-1 mr-2">
                    <div className="font-semibold text-gray-200 truncate">{displayName}</div>
                    <div className="text-[10px] text-gray-500 font-mono truncate">
                      {isCustom ? 'Custom slug' : currentProviderModels[m.display] || m.id || m.display}
                    </div>
                  </div>
                  {models.length > 1 && (
                    <button
                      onClick={() => setModels(models.filter((_, i) => i !== idx))}
                      className="p-1 text-gray-500 hover:text-red-400 rounded hover:bg-gray-800 transition"
                      title="Remove model"
                    >
                      <Minus className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <button
            onClick={() => setIsBrowseModalOpen(true)}
            className="w-full py-2 bg-[#32C4B7]/20 hover:bg-[#32C4B7]/30 text-[#32C4B7] border border-[#32C4B7]/50 rounded-md text-xs flex justify-center items-center font-bold gap-1.5 transition shadow-sm"
          >
            🔍 Browse & Select Models
          </button>
        </div>

        {/* API Key & Test Connection */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-400 flex items-center">
            <Key className="mr-1.5 h-4 w-4" /> API Key ({provider === 'groq' ? 'Groq' : 'OpenRouter'})
          </label>
          <input
            type="password"
            placeholder="Enter API key..."
            className="w-full bg-[#1f2937] border border-gray-700 rounded-md p-2.5 text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7] mb-2 text-sm"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <button
            onClick={onTestConnection}
            disabled={isTesting}
            className="w-full py-2 bg-[#374151] hover:bg-[#4b5563] text-gray-200 rounded-md text-sm flex justify-center items-center font-medium transition"
          >
            {isTesting ? <Loader2 className="animate-spin h-4 w-4" /> : '🔌 Test Connection'}
          </button>
          {testStatus && (
            <div
              className={`mt-3 p-3 rounded text-xs border ${
                testStatus.success
                  ? 'bg-green-900/10 text-green-400 border-green-900/50'
                  : 'bg-red-900/10 text-red-400 border-red-900/50'
              }`}
            >
              <div className="font-semibold mb-1 flex items-center">
                {testStatus.success ? (
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                ) : (
                  <XCircle className="w-3.5 h-3.5 mr-1.5" />
                )}
                {testStatus.success ? 'Success' : 'Connection Failed'}
              </div>
              {Object.entries(testStatus.messages).map(([k, v]) => (
                <div key={k} className="mt-1 opacity-90 truncate leading-relaxed" title={`${k}: ${v}`}>
                  - {k}: {v}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dataset Upload */}
        <div className="bg-[#1f2937]/30 border border-gray-700 p-4 rounded-lg space-y-3">
          <label className="block text-sm font-medium text-gray-300">📁 Custom Dataset (Optional)</label>
          <input
            type="file"
            accept=".csv,.xlsx"
            onChange={(e) => setDatasetFile(e.target.files ? e.target.files[0] : null)}
            className="w-full text-sm text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#374151] file:text-white hover:file:bg-[#4b5563]"
          />
          {datasetFile && (
            <p className="text-xs text-[#32C4B7] truncate">Selected: {datasetFile.name}</p>
          )}
          {task && (
            <p className="text-xs text-gray-500 mt-1">
              Required cols:{' '}
              {task === 'summarization'
                ? 'text, summary'
                : task === 'question_answering'
                ? 'text, question, answer'
                : 'text, sarcasm'}
            </p>
          )}
        </div>

        {/* Advanced Settings */}
        <div className="bg-[#1f2937]/30 border border-gray-700 p-4 rounded-lg space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">Samples (N)</label>
            <input
              type="number"
              min="1"
              max="1000"
              value={numSamples}
              onChange={(e) => setNumSamples(Number(e.target.value))}
              className="w-full bg-[#1f2937] border border-gray-700 rounded p-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
            />
          </div>

          {/* Checkpoint Mode */}
          <div className="pt-2 border-t border-gray-700/50">
            <label className="flex items-center text-sm font-medium text-gray-300 mb-2 cursor-pointer group">
              <input
                type="checkbox"
                className="mr-2 rounded border-gray-700 text-[#32C4B7] focus:ring-[#32C4B7]"
                checked={enableCheckpointMode}
                onChange={(e) => setEnableCheckpointMode(e.target.checked)}
              />
              💾 Enable Checkpoint Mode
            </label>
            {enableCheckpointMode && (
              <div className="mt-2 ml-6">
                <label className="block text-xs text-gray-400 mb-1">Save Every N Samples</label>
                <input
                  type="number"
                  min="10"
                  max="500"
                  step="10"
                  value={checkpointInterval}
                  onChange={(e) => setCheckpointInterval(Number(e.target.value))}
                  className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                />
              </div>
            )}
          </div>

          {/* Semantic Evaluation */}
          {task !== 'sarcasm' && (
            <div className="pt-2 border-t border-gray-700/50">
              <label className="flex items-center text-sm font-medium text-gray-300 mb-2 cursor-pointer group">
                <input
                  type="checkbox"
                  className="mr-2 rounded border-gray-700 text-[#32C4B7] focus:ring-[#32C4B7]"
                  checked={useSemanticMatching}
                  onChange={(e) => setUseSemanticMatching(e.target.checked)}
                />
                <BrainCircuit className="h-4 w-4 mr-1 text-[#4FC3F7] group-hover:text-[#29b6f6]" /> Use Semantic Eval
              </label>
              {useSemanticMatching && (
                <div className="space-y-2 mt-2 ml-6">
                  {!isCustomGemini ? (
                    <select
                      className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                      value={geminiModel}
                      onChange={(e) => {
                        if (e.target.value === 'custom') {
                          setIsCustomGemini(true);
                          setGeminiModel('');
                        } else {
                          setGeminiModel(e.target.value);
                        }
                      }}
                    >
                      {DEFAULT_GEMINI_CATALOG.map((g) => (
                        <option key={g.id} value={g.id}>
                          {g.name} ({g.speed})
                        </option>
                      ))}
                      <option value="custom">➕ Plug Custom Gemini Model...</option>
                    </select>
                  ) : (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <label className="text-[10px] text-gray-400">Custom Gemini Model ID:</label>
                        <button
                          type="button"
                          onClick={() => {
                            setIsCustomGemini(false);
                            setGeminiModel(DEFAULT_GEMINI_CATALOG[0].id);
                          }}
                          className="text-[10px] text-[#32C4B7] hover:underline"
                        >
                          Use Standard Models
                        </button>
                      </div>
                      <input
                        type="text"
                        placeholder="e.g. gemini-1.5-pro-latest"
                        value={geminiModel}
                        onChange={(e) => setGeminiModel(e.target.value)}
                        className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                      />
                    </div>
                  )}

                  <input
                    type="password"
                    placeholder="Gemini API Key required"
                    value={geminiApiKey}
                    onChange={(e) => setGeminiApiKey(e.target.value)}
                    className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Global Run Action Button */}
      <div className="mt-8 pt-4 border-t border-gray-800">
        <button
          onClick={onRunBenchmark}
          disabled={isRunning || !apiKey}
          className={`w-full py-3.5 font-semibold text-sm rounded-lg flex items-center justify-center transition-all duration-200 shadow-lg ${
            isRunning
              ? 'bg-[#1f2937] text-gray-500 cursor-not-allowed shadow-none'
              : 'bg-[#32C4B7] hover:bg-[#2aa69b] text-[#0b0f19]'
          }`}
        >
          {isRunning ? (
            <Loader2 className="animate-spin mr-2 h-4 w-4" />
          ) : (
            <Play className="mr-2 h-4 w-4 fill-current" />
          )}
          {isRunning ? 'Running...' : 'Run Benchmark'}
        </button>
      </div>

      {/* Browse Models Modal */}
      <BrowseModelsModal
        isOpen={isBrowseModalOpen}
        onClose={() => setIsBrowseModalOpen(false)}
        provider={provider}
        selectedModelIds={models.map((m) =>
          m.id || (m.display === 'Other (custom)' && m.custom ? m.custom : currentProviderModels[m.display] || m.display)
        )}
        onApplySelection={handleApplyBrowseModels}
      />
    </aside>
  );
};
