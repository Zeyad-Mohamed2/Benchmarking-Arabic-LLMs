import { LeaderboardEntry, ProgressState, BenchmarkResults, TaskType, ProviderType } from '../types';

export const API_BASE = (import.meta.env.VITE_API_BASE as string) || '/api';

export const OPENROUTER_MODELS: Record<string, string> = {
  "Google Gemma 3 27B IT": "google/gemma-3-27b-it:free",
  "OpenAI GPT-OSS 20B": "openai/gpt-oss-20b:free",
  "Qwen 3 4B": "qwen/qwen3-4b:free",
  "Cohere Command R7B": "cohere/command-r7b-12-2024",
  "Meta Llama 3.3 70B Instruct": "meta-llama/llama-3.3-70b-instruct:free",
  "Other (custom)": "Other (custom)"
};

export const GROQ_MODELS: Record<string, string> = {
  "OpenAI GPT-OSS 20B": "openai/gpt-oss-20b",
  "Qwen 3 32B": "qwen/qwen3-32b",
  "Llama 4 Maverick 17B 128E": "meta-llama/llama-4-maverick-17b-128e-instruct",
  "Kimi K2 0905": "moonshotai/kimi-k2-instruct-0905",
  "Other (custom)": "Other (custom)"
};

export async function testConnection(provider: string, apiKey: string, models: string[]) {
  const res = await fetch(`${API_BASE}/test-connection`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key: apiKey, models }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Connection test failed');
  return data;
}

export interface RunBenchmarkParams {
  task: TaskType;
  provider: ProviderType;
  apiKey: string;
  models: string[];
  numSamples: number;
  customPrompt?: string | null;
  useSemanticMatching?: boolean;
  geminiApiKey?: string;
  geminiModel?: string;
  enableCheckpointMode?: boolean;
  checkpointInterval?: number;
  datasetFile?: File | null;
}

export async function runBenchmark(params: RunBenchmarkParams): Promise<{ run_id: string }> {
  const formData = new FormData();
  formData.append('task', params.task);
  formData.append('provider', params.provider);
  formData.append('api_key', params.apiKey);
  formData.append('models', params.models.join(','));
  formData.append('number_of_samples', params.numSamples.toString());
  if (params.customPrompt) formData.append('custom_prompt', params.customPrompt);
  formData.append('use_semantic_matching', Boolean(params.useSemanticMatching).toString());
  if (params.useSemanticMatching && params.geminiApiKey) {
    formData.append('gemini_api_key', params.geminiApiKey);
    if (params.geminiModel) formData.append('gemini_model_name', params.geminiModel);
  }
  formData.append('enable_checkpoint_mode', Boolean(params.enableCheckpointMode).toString());
  if (params.checkpointInterval) {
    formData.append('checkpoint_interval', params.checkpointInterval.toString());
  }
  if (params.datasetFile) {
    formData.append('dataset', params.datasetFile);
  }

  const res = await fetch(`${API_BASE}/run-benchmark`, {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to start benchmark');
  return data;
}

export function createProgressStream(
  runId: string,
  onProgress: (progress: ProgressState) => void,
  onDone: (results: BenchmarkResults) => void,
  onError: (error: string) => void
): EventSource {
  const eventSource = new EventSource(`${API_BASE}/progress/${runId}`);

  eventSource.addEventListener('progress', (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      onProgress(data);
    } catch (err) {
      console.error('Error parsing progress SSE:', err);
    }
  });

  eventSource.addEventListener('done', (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      onDone(data);
    } catch (err) {
      console.error('Error parsing done SSE:', err);
    }
  });

  eventSource.addEventListener('error', (e: any) => {
    onError(e?.data || 'Connection lost to benchmark server');
  });

  return eventSource;
}

export async function fetchLeaderboard(): Promise<{ success: boolean; data: Record<string, LeaderboardEntry[]>; error?: string }> {
  const res = await fetch(`${API_BASE}/leaderboard`);
  const data = await res.json();
  return data;
}

export async function promoteToLeaderboard(
  task: string,
  model: string,
  scores: any,
  totalSamples: number = 1000,
  semanticMatchRate?: number
): Promise<{ success: boolean; data?: Record<string, LeaderboardEntry[]>; error?: string }> {
  const res = await fetch(`${API_BASE}/leaderboard/promote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      task,
      model,
      scores,
      total_samples: totalSamples,
      semantic_match_rate: semanticMatchRate,
    }),
  });
  const data = await res.json();
  return data;
}
