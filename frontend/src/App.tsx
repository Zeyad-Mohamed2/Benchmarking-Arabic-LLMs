import { useState, useEffect } from 'react';
import { XCircle } from 'lucide-react';
import {
  TaskType,
  ProviderType,
  ModelSelection,
  ProgressState,
  BenchmarkResults,
  LeaderboardEntry,
} from './types';
import {
  API_BASE,
  testConnection,
  runBenchmark,
  createProgressStream,
  fetchLeaderboard,
} from './services/api';
import { Header } from './components/layout/Header';
import { ConfigSidebar } from './components/sidebar/ConfigSidebar';
import { StatusCards } from './components/benchmark/StatusCards';
import { ProgressMonitor } from './components/benchmark/ProgressMonitor';
import { ResultsViewer } from './components/benchmark/ResultsViewer';
import { LeaderboardView } from './components/leaderboard/LeaderboardView';

const OPENROUTER_MODELS: Record<string, string> = {
  'Google Gemma 3 27B IT': 'google/gemma-3-27b-it:free',
  'OpenAI GPT-OSS 20B': 'openai/gpt-oss-20b:free',
  'Qwen 3 4B': 'qwen/qwen3-4b:free',
  'Cohere Command R7B': 'cohere/command-r7b-12-2024',
  'Meta Llama 3.3 70B Instruct': 'meta-llama/llama-3.3-70b-instruct:free',
  'Other (custom)': 'Other (custom)',
};

const GROQ_MODELS: Record<string, string> = {
  'OpenAI GPT-OSS 20B': 'openai/gpt-oss-20b',
  'Qwen 3 32B': 'qwen/qwen3-32b',
  'Llama 4 Maverick 17B 128E': 'meta-llama/llama-4-maverick-17b-128e-instruct',
  'Kimi K2 0905': 'moonshotai/kimi-k2-instruct-0905',
  'Other (custom)': 'Other (custom)',
};

export default function App() {
  const [task, setTask] = useState<TaskType>('question_answering');
  const [provider, setProvider] = useState<ProviderType>('openrouter');
  const [apiKey, setApiKey] = useState('');
  const [numSamples, setNumSamples] = useState(1);
  const [customPrompt, setCustomPrompt] = useState<string | null>(null);

  // Model Selectors
  const [models, setModels] = useState<ModelSelection[]>([
    { display: Object.keys(OPENROUTER_MODELS)[0], custom: '' },
  ]);

  // Semantic Matching
  const [useSemanticMatching, setUseSemanticMatching] = useState(false);
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash-lite');

  // Checkpoint Mode
  const [enableCheckpointMode, setEnableCheckpointMode] = useState(false);
  const [checkpointInterval, setCheckpointInterval] = useState(50);

  // Dataset
  const [datasetFile, setDatasetFile] = useState<File | null>(null);

  // Execution State
  const [runId, setRunId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [results, setResults] = useState<BenchmarkResults | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Leaderboard State
  const [mainView, setMainView] = useState<'benchmark' | 'leaderboard'>('benchmark');
  const [leaderboardData, setLeaderboardData] = useState<Record<string, LeaderboardEntry[]> | null>(null);
  const [leaderboardTask, setLeaderboardTask] = useState<TaskType>('question_answering');
  const [isLoadingLeaderboard, setIsLoadingLeaderboard] = useState(false);
  const [leaderboardError, setLeaderboardError] = useState<string | null>(null);

  // Connection Test
  const [testStatus, setTestStatus] = useState<{ success: boolean; messages: Record<string, string> } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // Update models dropdown automatically when changing providers
  useEffect(() => {
    const opts = provider === 'groq' ? GROQ_MODELS : OPENROUTER_MODELS;
    const defaultKey = Object.keys(opts)[0];
    setModels((prev) =>
      prev.map((m) => {
        if (opts[m.display]) return m;
        return { display: defaultKey, custom: '' };
      })
    );
  }, [provider]);

  // Compile active models list
  const getCompiledModelsList = () => {
    const opts = provider === 'groq' ? GROQ_MODELS : OPENROUTER_MODELS;
    return models
      .map((m) => (m.display === 'Other (custom)' && m.custom ? m.custom : opts[m.display]))
      .filter(Boolean);
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestStatus(null);
    try {
      const activeModels = getCompiledModelsList();
      if (activeModels.length === 0) throw new Error('Please select at least one active model');

      const data = await testConnection(provider, apiKey, activeModels);
      setTestStatus(data);
    } catch (err: any) {
      setTestStatus({ success: false, messages: { Error: err.message } });
    } finally {
      setIsTesting(false);
    }
  };

  const handleRunBenchmark = async () => {
    if (!apiKey) return alert('Provider API Key is required');
    if (useSemanticMatching && !geminiApiKey) return alert('Gemini API Key required for semantic matching');

    setIsRunning(true);
    setErrorMsg(null);
    setProgress(null);
    setResults(null);

    try {
      const activeModels = getCompiledModelsList();
      const data = await runBenchmark({
        task,
        provider,
        apiKey,
        models: activeModels,
        numSamples,
        customPrompt,
        useSemanticMatching,
        geminiApiKey,
        geminiModel,
        enableCheckpointMode,
        checkpointInterval,
        datasetFile,
      });

      setRunId(data.run_id);
    } catch (err: any) {
      setErrorMsg(err.message);
      setIsRunning(false);
    }
  };

  // SSE Progress Stream
  useEffect(() => {
    if (!runId) return;

    const eventSource = createProgressStream(
      runId,
      (prog: ProgressState) => setProgress(prog),
      (res: BenchmarkResults) => {
        setResults(res);
        setIsRunning(false);
      },
      (err: string) => {
        setErrorMsg(err);
        setIsRunning(false);
      }
    );

    return () => {
      eventSource.close();
    };
  }, [runId]);

  // Fetch Leaderboard
  useEffect(() => {
    if (mainView === 'leaderboard' && !leaderboardData) {
      setIsLoadingLeaderboard(true);
      setLeaderboardError(null);
      fetchLeaderboard()
        .then((res) => {
          if (res.success && res.data) {
            setLeaderboardData(res.data);
          } else {
            setLeaderboardError(res.error || 'Failed to load leaderboard data');
          }
        })
        .catch((err: any) => setLeaderboardError(err.message))
        .finally(() => setIsLoadingLeaderboard(false));
    }
  }, [mainView, leaderboardData]);

  return (
    <div className="flex h-screen bg-[#0b0f19] text-gray-200 overflow-hidden font-sans">
      {/* Sidebar Configuration */}
      {mainView === 'benchmark' && (
        <ConfigSidebar
          task={task}
          setTask={setTask}
          provider={provider}
          setProvider={setProvider}
          apiKey={apiKey}
          setApiKey={setApiKey}
          models={models}
          setModels={setModels}
          numSamples={numSamples}
          setNumSamples={setNumSamples}
          datasetFile={datasetFile}
          setDatasetFile={setDatasetFile}
          useSemanticMatching={useSemanticMatching}
          setUseSemanticMatching={setUseSemanticMatching}
          geminiApiKey={geminiApiKey}
          setGeminiApiKey={setGeminiApiKey}
          geminiModel={geminiModel}
          setGeminiModel={setGeminiModel}
          enableCheckpointMode={enableCheckpointMode}
          setEnableCheckpointMode={setEnableCheckpointMode}
          checkpointInterval={checkpointInterval}
          setCheckpointInterval={setCheckpointInterval}
          isRunning={isRunning}
          isTesting={isTesting}
          testStatus={testStatus}
          onTestConnection={handleTestConnection}
          onRunBenchmark={handleRunBenchmark}
          openRouterModels={OPENROUTER_MODELS}
          groqModels={GROQ_MODELS}
        />
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 relative bg-gradient-to-br from-[#0b0f19] to-[#111827]">
        <Header mainView={mainView} setMainView={setMainView} />

        {/* Dashboard Stage */}
        <div className="p-10 flex-1 overflow-y-auto scrollbar-thin">
          {mainView === 'leaderboard' ? (
            <LeaderboardView
              leaderboardData={leaderboardData}
              isLoading={isLoadingLeaderboard}
              error={leaderboardError}
              activeTask={leaderboardTask}
              setActiveTask={setLeaderboardTask}
            />
          ) : (
            <>
              {errorMsg && (
                <div className="mb-8 bg-red-950 border border-red-900 text-red-200 px-5 py-4 rounded-xl flex items-start shadow-xl">
                  <XCircle className="w-5 h-5 mr-3 shrink-0 mt-0.5 text-red-400" />
                  <span className="leading-relaxed">{errorMsg}</span>
                </div>
              )}

              {/* Status and Prompt Cards */}
              {(!results?.success || isRunning) && (
                <StatusCards
                  task={task}
                  models={models}
                  numSamples={numSamples}
                  useSemanticMatching={useSemanticMatching}
                  customPrompt={customPrompt}
                  setCustomPrompt={setCustomPrompt}
                />
              )}

              {/* Progress Monitor */}
              <ProgressMonitor isRunning={isRunning} progress={progress} />

              {/* Results Viewer */}
              {results?.success && <ResultsViewer results={results} task={task} apiBase={API_BASE} />}
            </>
          )}
        </div>
      </main>
    </div>
  );
}