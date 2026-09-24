import React from 'react';
import { Settings, Play, Database, Key, Loader2, Plus, Minus, BrainCircuit, CheckCircle2, XCircle } from 'lucide-react';
import { TaskType, ProviderType, ModelSelection } from '../../types';

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
  const currentProviderModels = provider === 'groq' ? groqModels : openRouterModels;

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

        {/* Model Selection */}
        <div className="bg-[#1f2937]/30 border border-gray-700 p-4 rounded-lg">
          <div className="flex justify-between items-center mb-3">
            <label className="text-sm font-medium text-gray-300 flex items-center">
              <Database className="mr-1.5 h-4 w-4 text-[#32C4B7]" /> Select Models
            </label>
          </div>

          {models.map((m, idx) => (
            <div key={idx} className="mb-3 relative group">
              <label className="block text-xs text-gray-500 mb-1">Model {idx + 1}</label>
              <div className="flex gap-2">
                <div className="flex-1 space-y-2">
                  <select
                    className="w-full bg-[#1f2937] border border-gray-700 rounded p-2 text-sm text-gray-200 focus:outline-none focus:border-[#32C4B7]"
                    value={m.display}
                    onChange={(e) => {
                      const newMw = [...models];
                      newMw[idx].display = e.target.value;
                      setModels(newMw);
                    }}
                  >
                    {Object.keys(currentProviderModels).map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>

                  {m.display === 'Other (custom)' && (
                    <input
                      type="text"
                      placeholder="e.g. meta-llama/llama-3..."
                      className="w-full bg-[#111827] border border-gray-700 rounded p-2 text-sm text-gray-200 focus:outline-none focus:border-[#32C4B7]"
                      value={m.custom}
                      onChange={(e) => {
                        const n = [...models];
                        n[idx].custom = e.target.value;
                        setModels(n);
                      }}
                    />
                  )}
                </div>
                {models.length > 1 && (
                  <button
                    onClick={() => setModels(models.filter((_, i) => i !== idx))}
                    className="mt-1 h-[34px] px-2 text-gray-500 hover:text-red-400 bg-gray-800/50 hover:bg-gray-800 rounded border border-transparent"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}

          {models.length < 3 && (
            <button
              onClick={() =>
                setModels([...models, { display: Object.keys(currentProviderModels)[0], custom: '' }])
              }
              className="text-xs flex items-center text-[#32C4B7] hover:text-[#2aa69b] font-medium transition-colors"
            >
              <Plus className="h-3 w-3 mr-1" /> Add Model
            </button>
          )}
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
                  <select
                    className="w-full bg-[#111827] border border-gray-700 rounded p-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-[#32C4B7]"
                    value={geminiModel}
                    onChange={(e) => setGeminiModel(e.target.value)}
                  >
                    <option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite</option>
                    <option value="gemini-2.5-flash">gemini-2.5-flash</option>
                    <option value="gemini-2.5-pro">gemini-2.5-pro</option>
                    <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                    <option value="gemini-2.0-flash-lite">gemini-2.0-flash-lite</option>
                    <option value="gemini-2.0-pro">gemini-2.0-pro</option>
                  </select>
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
    </aside>
  );
};
