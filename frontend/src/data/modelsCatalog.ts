import { ModelCatalogItem, GeminiCatalogItem } from '../types';

export const DEFAULT_MODELS_CATALOG: ModelCatalogItem[] = [
  // OpenRouter Models
  {
    id: 'google/gemma-3-27b-it:free',
    name: 'Google Gemma 3 27B IT',
    provider: 'openrouter',
    paramSize: '27B',
    isFree: true,
    contextWindow: '8k',
    description: 'Strong multilingual performance with state-of-the-art Arabic synthesis.',
    tags: ['Arabic-tuned', 'High Quality', 'Free'],
  },
  {
    id: 'openai/gpt-oss-20b:free',
    name: 'OpenAI GPT-OSS 20B',
    provider: 'openrouter',
    paramSize: '20B',
    isFree: true,
    contextWindow: '8k',
    description: 'Balanced instruction-tuned model suitable for multi-turn Q&A.',
    tags: ['Balanced', 'Free'],
  },
  {
    id: 'qwen/qwen3-4b:free',
    name: 'Qwen 3 4B',
    provider: 'openrouter',
    paramSize: '4B',
    isFree: true,
    contextWindow: '32k',
    description: 'Compact high-efficiency Arabic & multilingual reasoning model.',
    tags: ['Lightweight', 'Fast', 'Free'],
  },
  {
    id: 'meta-llama/llama-3.3-70b-instruct:free',
    name: 'Meta Llama 3.3 70B Instruct',
    provider: 'openrouter',
    paramSize: '70B',
    isFree: true,
    contextWindow: '128k',
    description: 'Flagship open-weights model with exceptional nuance and reasoning.',
    tags: ['Flagship', 'High Reasoning', 'Free'],
  },
  {
    id: 'cohere/command-r7b-12-2024',
    name: 'Cohere Command R7B',
    provider: 'openrouter',
    paramSize: '7B',
    isFree: false,
    contextWindow: '128k',
    description: 'Optimized for RAG, multilingual translation, and complex extraction.',
    tags: ['Multilingual', 'RAG-Ready'],
  },
  {
    id: 'mistralai/mistral-large-2411',
    name: 'Mistral Large 2411',
    provider: 'openrouter',
    paramSize: '123B',
    isFree: false,
    contextWindow: '128k',
    description: 'Frontier reasoning capability across Arabic complex syntax.',
    tags: ['Frontier', 'High Accuracy'],
  },
  {
    id: 'qwen/qwen-2.5-72b-instruct',
    name: 'Qwen 2.5 72B Instruct',
    provider: 'openrouter',
    paramSize: '72B',
    isFree: false,
    contextWindow: '128k',
    description: 'World-class multilingual comprehension and Arabic benchmark leader.',
    tags: ['Benchmark Leader', 'Top Tier'],
  },

  // Groq Models
  {
    id: 'openai/gpt-oss-20b',
    name: 'OpenAI GPT-OSS 20B (Groq LPU)',
    provider: 'groq',
    paramSize: '20B',
    isFree: true,
    contextWindow: '8k',
    description: 'Accelerated on Groq LPUs for sub-second generation latency.',
    tags: ['Ultra-Fast', 'Free'],
  },
  {
    id: 'qwen/qwen3-32b',
    name: 'Qwen 3 32B (Groq LPU)',
    provider: 'groq',
    paramSize: '32B',
    isFree: true,
    contextWindow: '32k',
    description: 'Top-tier Arabic capability accelerated on hardware LPUs.',
    tags: ['High Quality', 'Ultra-Fast', 'Free'],
  },
  {
    id: 'meta-llama/llama-4-maverick-17b-128e-instruct',
    name: 'Llama 4 Maverick 17B',
    provider: 'groq',
    paramSize: '17B',
    isFree: true,
    contextWindow: '128k',
    description: 'Next-gen architecture with broad multilingual contextual awareness.',
    tags: ['Experimental', 'Ultra-Fast', 'Free'],
  },
  {
    id: 'moonshotai/kimi-k2-instruct-0905',
    name: 'Kimi K2 0905',
    provider: 'groq',
    paramSize: '32B',
    isFree: true,
    contextWindow: '32k',
    description: 'Excels in Arabic summarization and long-sequence synthesis.',
    tags: ['Long Context', 'Ultra-Fast', 'Free'],
  },
];

export const DEFAULT_GEMINI_CATALOG: GeminiCatalogItem[] = [
  {
    id: 'gemini-2.5-flash-lite',
    name: 'Gemini 2.5 Flash Lite',
    speed: 'Ultra Fast',
    tier: 'Lowest Cost / Fast',
    description: 'Recommended for rapid evaluation across hundreds of samples.',
  },
  {
    id: 'gemini-2.5-flash',
    name: 'Gemini 2.5 Flash',
    speed: 'Fast',
    tier: 'Balanced',
    description: 'Enhanced semantic nuance for complex Arabic rhetoric.',
  },
  {
    id: 'gemini-2.5-pro',
    name: 'Gemini 2.5 Pro',
    speed: 'High Reasoning',
    tier: 'Deep Evaluator',
    description: 'Best-in-class judgment for subtle sarcasm and figurative speech.',
  },
  {
    id: 'gemini-2.0-flash',
    name: 'Gemini 2.0 Flash',
    speed: 'Fast',
    tier: 'Standard',
    description: 'Stable generation model for general multilingual benchmarking.',
  },
];

const LOCAL_STORAGE_CUSTOM_MODELS_KEY = 'arabic_llm_custom_models';
const LOCAL_STORAGE_CUSTOM_GEMINI_KEY = 'arabic_llm_custom_gemini';

export function getCustomModels(): ModelCatalogItem[] {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_CUSTOM_MODELS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

export function saveCustomModel(model: ModelCatalogItem): ModelCatalogItem[] {
  const existing = getCustomModels();
  const filtered = existing.filter(m => m.id !== model.id);
  const updated = [model, ...filtered];
  try {
    localStorage.setItem(LOCAL_STORAGE_CUSTOM_MODELS_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to save custom model to localStorage', e);
  }
  return updated;
}

export function removeCustomModel(modelId: string): ModelCatalogItem[] {
  const existing = getCustomModels();
  const updated = existing.filter(m => m.id !== modelId);
  try {
    localStorage.setItem(LOCAL_STORAGE_CUSTOM_MODELS_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to remove custom model from localStorage', e);
  }
  return updated;
}

export function getAllModels(provider?: string): ModelCatalogItem[] {
  const custom = getCustomModels();
  const combined = [...custom, ...DEFAULT_MODELS_CATALOG];
  if (!provider) return combined;
  return combined.filter(m => m.provider === provider);
}

export function getCustomGeminiModels(): GeminiCatalogItem[] {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_CUSTOM_GEMINI_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

export function saveCustomGeminiModel(model: GeminiCatalogItem): GeminiCatalogItem[] {
  const existing = getCustomGeminiModels();
  const filtered = existing.filter(m => m.id !== model.id);
  const updated = [model, ...filtered];
  try {
    localStorage.setItem(LOCAL_STORAGE_CUSTOM_GEMINI_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error('Failed to save custom gemini model to localStorage', e);
  }
  return updated;
}
