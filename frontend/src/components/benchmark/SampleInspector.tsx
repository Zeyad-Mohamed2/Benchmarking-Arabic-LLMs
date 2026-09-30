import React, { useState, useMemo } from 'react';
import { SampleItem, TaskType } from '../../types';
import { 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle2, 
  XCircle, 
  Sparkles, 
  Copy, 
  Check, 
  HelpCircle,
  Eye,
  Layers
} from 'lucide-react';

interface SampleInspectorProps {
  samples: SampleItem[];
  task: TaskType;
}

export const SampleInspector: React.FC<SampleInspectorProps> = ({ samples, task }) => {
  const [selectedExampleNum, setSelectedExampleNum] = useState<number>(() => {
    return samples.length > 0 ? samples[0].example_number : 1;
  });
  const [statusFilter, setStatusFilter] = useState<'all' | 'match' | 'mismatch'>('all');
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Extract unique example numbers
  const exampleNumbers = useMemo(() => {
    const nums = Array.from(new Set(samples.map(s => s.example_number))).sort((a, b) => a - b);
    return nums;
  }, [samples]);

  // Extract unique models
  const uniqueModels = useMemo(() => {
    return Array.from(new Set(samples.map(s => s.model))).sort();
  }, [samples]);

  // Filter example numbers based on statusFilter and modelFilter
  const filteredExampleNumbers = useMemo(() => {
    return exampleNumbers.filter(num => {
      const numSamples = samples.filter(s => s.example_number === num);
      if (modelFilter !== 'all') {
        const forModel = numSamples.find(s => s.model === modelFilter);
        if (!forModel) return false;
        if (statusFilter === 'match' && !forModel.match) return false;
        if (statusFilter === 'mismatch' && forModel.match) return false;
        return true;
      }

      if (statusFilter === 'match') {
        return numSamples.some(s => s.match);
      }
      if (statusFilter === 'mismatch') {
        return numSamples.some(s => !s.match);
      }
      return true;
    });
  }, [exampleNumbers, samples, statusFilter, modelFilter]);

  // Keep selectedExampleNum in sync with filters
  const currentExampleNum = useMemo(() => {
    if (filteredExampleNumbers.includes(selectedExampleNum)) {
      return selectedExampleNum;
    }
    return filteredExampleNumbers.length > 0 ? filteredExampleNumbers[0] : selectedExampleNum;
  }, [filteredExampleNumbers, selectedExampleNum]);

  // Get all model samples for the current example
  const currentSamples = useMemo(() => {
    let list = samples.filter(s => s.example_number === currentExampleNum);
    if (modelFilter !== 'all') {
      list = list.filter(s => s.model === modelFilter);
    }
    return list;
  }, [samples, currentExampleNum, modelFilter]);

  // Context & expected output (from the first sample of this example)
  const baseSample = samples.find(s => s.example_number === currentExampleNum) || samples[0];

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const currentIndex = filteredExampleNumbers.indexOf(currentExampleNum);
  const canGoPrev = currentIndex > 0;
  const canGoNext = currentIndex < filteredExampleNumbers.length - 1;

  const goToPrev = () => {
    if (canGoPrev) {
      setSelectedExampleNum(filteredExampleNumbers[currentIndex - 1]);
    }
  };

  const goToNext = () => {
    if (canGoNext) {
      setSelectedExampleNum(filteredExampleNumbers[currentIndex + 1]);
    }
  };

  if (!samples || samples.length === 0) {
    return (
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-12 text-center">
        <div className="w-12 h-12 rounded-full bg-[#1f2937] text-gray-400 flex items-center justify-center mx-auto mb-3">
          <Eye className="w-6 h-6 text-[#32C4B7]" />
        </div>
        <h4 className="text-lg font-bold text-white mb-1">No Sample Logs Available</h4>
        <p className="text-sm text-gray-400 max-w-md mx-auto">
          Detailed sample logs are recorded automatically during benchmark runs. Run a benchmark with at least 1 sample to inspect prompts and outputs side-by-side.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Filter & Navigation Bar */}
      <div className="bg-[#1f2937]/50 border border-gray-700/60 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        {/* Navigation & Example Counter */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center bg-[#111827] border border-gray-700 rounded-lg p-1">
            <button
              onClick={goToPrev}
              disabled={!canGoPrev}
              className="p-1.5 rounded hover:bg-gray-800 text-gray-300 disabled:opacity-30 disabled:hover:bg-transparent transition"
              title="Previous sample"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-xs font-mono font-semibold text-[#32C4B7]">
              Sample {currentIndex >= 0 ? currentIndex + 1 : 1} / {filteredExampleNumbers.length}
            </span>
            <button
              onClick={goToNext}
              disabled={!canGoNext}
              className="p-1.5 rounded hover:bg-gray-800 text-gray-300 disabled:opacity-30 disabled:hover:bg-transparent transition"
              title="Next sample"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Jump to specific example */}
          <select
            value={currentExampleNum}
            onChange={(e) => setSelectedExampleNum(Number(e.target.value))}
            className="bg-[#111827] border border-gray-700 text-xs text-gray-200 rounded-lg px-2.5 py-1.5 focus:border-[#32C4B7] focus:outline-none font-mono"
          >
            {filteredExampleNumbers.map((num) => (
              <option key={num} value={num}>
                Example #{num}
              </option>
            ))}
          </select>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Match Filter */}
          <div className="flex items-center bg-[#111827] border border-gray-700 rounded-lg p-0.5 text-xs">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-2.5 py-1 rounded transition ${
                statusFilter === 'all'
                  ? 'bg-[#32C4B7] text-[#0b0f19] font-bold'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              All ({exampleNumbers.length})
            </button>
            <button
              onClick={() => setStatusFilter('match')}
              className={`px-2.5 py-1 rounded transition flex items-center ${
                statusFilter === 'match'
                  ? 'bg-emerald-500 text-white font-bold'
                  : 'text-gray-400 hover:text-emerald-400'
              }`}
            >
              <CheckCircle2 className="w-3 h-3 mr-1" /> Matches
            </button>
            <button
              onClick={() => setStatusFilter('mismatch')}
              className={`px-2.5 py-1 rounded transition flex items-center ${
                statusFilter === 'mismatch'
                  ? 'bg-rose-500 text-white font-bold'
                  : 'text-gray-400 hover:text-rose-400'
              }`}
            >
              <XCircle className="w-3 h-3 mr-1" /> Mismatches
            </button>
          </div>

          {/* Model Filter */}
          {uniqueModels.length > 1 && (
            <select
              value={modelFilter}
              onChange={(e) => setModelFilter(e.target.value)}
              className="bg-[#111827] border border-gray-700 text-xs text-gray-200 rounded-lg px-2.5 py-1.5 focus:border-[#32C4B7] focus:outline-none"
            >
              <option value="all">All Models ({uniqueModels.length})</option>
              {uniqueModels.map((m) => (
                <option key={m} value={m}>
                  {m.replace(':free', '')}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Input Text & Expected Ground Truth Box */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Input Text / Question */}
        <div className="lg:col-span-7 bg-[#131b2e] border border-gray-700/60 rounded-xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 border-b border-gray-700/50 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#32C4B7] flex items-center">
                <Layers className="w-3.5 h-3.5 mr-1.5" /> Prompt Input / Context
              </span>
              <button
                onClick={() =>
                  handleCopy(
                    baseSample?.question
                      ? `${baseSample.input_text}\n\nالسؤال: ${baseSample.question}`
                      : baseSample?.input_text || '',
                    'prompt'
                  )
                }
                className="text-gray-400 hover:text-white transition p-1"
                title="Copy prompt"
              >
                {copiedKey === 'prompt' ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>

            {/* QA Question Display */}
            {baseSample?.question && (
              <div className="mb-3 p-3 bg-[#1e293b]/70 border border-teal-500/30 rounded-lg">
                <span className="text-xs font-semibold text-teal-300 block mb-1">السؤال (Question):</span>
                <p className="text-sm font-medium text-white leading-relaxed" dir="rtl">
                  {baseSample.question}
                </p>
              </div>
            )}

            {/* Main Text Content */}
            <div className="max-h-48 overflow-y-auto pr-1">
              <span className="text-xs font-semibold text-gray-400 block mb-1">النص المدخل (Input Text):</span>
              <p
                className="text-sm text-gray-200 leading-relaxed font-sans whitespace-pre-wrap"
                dir="rtl"
              >
                {baseSample?.input_text || '(Empty context)'}
              </p>
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-gray-700/40 text-[11px] text-gray-400 font-mono">
            Task: <span className="text-[#32C4B7]">{baseSample?.task || task}</span>
          </div>
        </div>

        {/* Expected Ground Truth */}
        <div className="lg:col-span-5 bg-[#0f2922] border border-emerald-500/40 rounded-xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 border-b border-emerald-500/30 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> Ground Truth (الإجابة المرجعية)
              </span>
              <button
                onClick={() => handleCopy(baseSample?.expected_output || '', 'expected')}
                className="text-emerald-400 hover:text-emerald-200 transition p-1"
                title="Copy ground truth"
              >
                {copiedKey === 'expected' ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>

            <div className="max-h-48 overflow-y-auto pr-1">
              <p
                className="text-sm font-medium text-emerald-100 leading-relaxed font-sans whitespace-pre-wrap"
                dir="rtl"
              >
                {baseSample?.expected_output || '(No reference provided)'}
              </p>
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-emerald-500/30 text-[11px] text-emerald-400/80 font-mono">
            Target Reference Standard
          </div>
        </div>
      </div>

      {/* Model Outputs Comparison Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-bold uppercase tracking-wider text-gray-300 flex items-center">
            <Sparkles className="w-4 h-4 mr-2 text-[#32C4B7]" />
            Model Predictions for Example #{currentExampleNum} ({currentSamples.length} models)
          </h4>
          <span className="text-xs text-gray-400">
            Side-by-side Arabic output and judge evaluation
          </span>
        </div>

        <div
          className={`grid gap-5 ${
            currentSamples.length === 1
              ? 'grid-cols-1'
              : currentSamples.length === 2
              ? 'grid-cols-1 md:grid-cols-2'
              : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
          }`}
        >
          {currentSamples.map((sample) => {
            const isMatch = sample.match;
            const isSemantic = sample.match_type === 'semantic';
            const confidence = sample.match_confidence;

            return (
              <div
                key={sample.model}
                className={`bg-[#111827] rounded-xl border flex flex-col justify-between transition-all duration-200 shadow-md ${
                  isMatch
                    ? 'border-emerald-500/40 hover:border-emerald-400/70'
                    : 'border-rose-500/40 hover:border-rose-400/70'
                }`}
              >
                {/* Header */}
                <div className="p-4 border-b border-gray-800 bg-[#162032]/60 rounded-t-xl">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span
                      className="font-bold text-sm text-white truncate"
                      title={sample.model}
                    >
                      {sample.model.replace(':free', '')}
                    </span>
                    <button
                      onClick={() => handleCopy(sample.model_output, `model_${sample.model}`)}
                      className="text-gray-400 hover:text-white transition p-1"
                      title="Copy output"
                    >
                      {copiedKey === `model_${sample.model}` ? (
                        <Check className="w-3.5 h-3.5 text-green-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  {/* Evaluation Match Badge */}
                  <div className="flex flex-wrap items-center gap-2">
                    {isMatch ? (
                      <span className="inline-flex items-center text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-900/50 text-emerald-300 border border-emerald-700/60">
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                        {isSemantic ? 'Semantic Match' : 'Exact Match'}
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-900/50 text-rose-300 border border-rose-700/60">
                        <XCircle className="w-3.5 h-3.5 mr-1" /> Mismatch
                      </span>
                    )}

                    {isSemantic && confidence !== null && confidence !== undefined && (
                      <span className="inline-flex items-center text-xs font-mono px-2 py-0.5 rounded-full bg-teal-900/40 text-teal-300 border border-teal-700/50">
                        Conf: {(Number(confidence) * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>

                {/* Model Output Body */}
                <div className="p-4 flex-1">
                  <span className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider block mb-1.5">
                    Model Generated Text:
                  </span>
                  <div className="p-3 bg-[#0b0f19] rounded-lg border border-gray-800/80 min-h-[100px] max-h-56 overflow-y-auto">
                    <p
                      className="text-sm text-gray-200 leading-relaxed font-sans whitespace-pre-wrap"
                      dir="rtl"
                    >
                      {sample.model_output || (
                        <span className="text-gray-500 italic">(Empty or error output)</span>
                      )}
                    </p>
                  </div>

                  {/* Judge Explanation if present */}
                  {sample.judge_explanation && sample.judge_explanation.trim() !== '' && (
                    <div className="mt-3 p-3 bg-[#1e293b]/60 border border-gray-700 rounded-lg text-xs">
                      <div className="flex items-center text-[#32C4B7] font-semibold mb-1">
                        <HelpCircle className="w-3.5 h-3.5 mr-1" />
                        <span>LLM Judge Reasoning:</span>
                      </div>
                      <p className="text-gray-300 text-[11px] leading-relaxed" dir="auto">
                        {sample.judge_explanation}
                      </p>
                    </div>
                  )}
                </div>

                {/* Card Footer with timestamp */}
                <div className="px-4 py-2 border-t border-gray-800/80 bg-[#0b0f19]/40 rounded-b-xl text-[10px] text-gray-500 font-mono flex items-center justify-between">
                  <span>Match Type: {sample.match_type}</span>
                  {sample.timestamp && <span>{sample.timestamp.split('T')[1]?.slice(0, 8)}</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
