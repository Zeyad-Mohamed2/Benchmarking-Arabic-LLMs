import React from 'react';
import { TaskType, ModelSelection } from '../../types';

interface StatusCardsProps {
  task: TaskType;
  models: ModelSelection[];
  numSamples: number;
  useSemanticMatching: boolean;
  customPrompt: string | null;
  setCustomPrompt: (prompt: string | null) => void;
}

export const StatusCards: React.FC<StatusCardsProps> = ({
  task,
  models,
  numSamples,
  useSemanticMatching,
  customPrompt,
  setCustomPrompt,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
      {/* Prompt Configuration */}
      <div className="md:col-span-2 bg-[#111827] border border-gray-700/50 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-bold text-white mb-4">Prompt Configuration</h3>
        <label className="flex items-center text-sm font-medium text-gray-300 mb-4 cursor-pointer group w-fit">
          <input
            type="checkbox"
            className="mr-2 rounded border-gray-700 text-[#32C4B7] focus:ring-[#32C4B7]"
            checked={customPrompt !== null}
            onChange={(e) => setCustomPrompt(e.target.checked ? '' : null)}
          />
          Use Custom Prompt Template
        </label>
        {customPrompt !== null ? (
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-white">Custom Prompt Template</h4>
            <textarea
              placeholder="Example: Analyze the sentiment: {text}"
              className="w-full h-28 bg-[#1f2937] border border-gray-700 rounded-md p-3 text-sm text-gray-200 focus:outline-none focus:border-[#32C4B7] resize-none"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
            ></textarea>
            {customPrompt && (
              <div className="text-xs bg-green-900/10 text-green-400 border border-green-900/50 p-2 rounded">
                ✅ Custom prompt will be used
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm bg-blue-900/10 text-blue-400 border border-blue-900/50 p-3 rounded">
            ℹ️ Default prompt template will be used
          </div>
        )}
      </div>

      {/* Benchmark Status */}
      <div className="md:col-span-1 bg-[#111827] border border-gray-700/50 rounded-xl p-6 shadow-lg">
        <h3 className="text-lg font-bold text-white mb-4">Benchmark Status</h3>
        <div className="space-y-2 text-sm text-gray-300">
          <p>
            <strong className="text-white">Task:</strong>{' '}
            {task === 'question_answering'
              ? 'Question Answering'
              : task === 'summarization'
              ? 'Text Summarization'
              : 'Sarcasm Detection'}
          </p>
          <p>
            <strong className="text-white">Models:</strong> {models.length}
          </p>
          <p>
            <strong className="text-white">Samples:</strong> {numSamples}
          </p>
          <p>
            <strong className="text-white">Dataset:</strong> Default
          </p>
          <p>
            <strong className="text-white">Evaluation:</strong>{' '}
            {useSemanticMatching ? 'Metrics + LLM as a Judge (Gemini)' : 'Metrics'}
          </p>
          <p className="mt-4 pt-4 border-t border-gray-700 text-xs text-gray-500">
            💡 API keys are only stored in memory for this session
          </p>
        </div>
      </div>
    </div>
  );
};
