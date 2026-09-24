export type TaskType = 'question_answering' | 'summarization' | 'sarcasm';

export type ProviderType = 'openrouter' | 'groq';

export interface ModelSelection {
  display: string;
  custom: string;
}

export interface ProgressState {
  current: number;
  total: number;
  status: string;
}

export interface ModelScores {
  Accuracy?: number;
  accuracy?: number;
  EM?: number;
  em?: number;
  F1?: number;
  f1?: number;
  Precision?: number;
  precision?: number;
  Recall?: number;
  recall?: number;
  ROC_AUC?: number;
  roc_auc?: number;
  ROUGE1?: number;
  rouge1?: number;
  ROUGEL?: number;
  rougeL?: number;
  ROUGE?: number;
  BLEU?: number;
  bleu?: number;
  METEOR?: number;
  meteor?: number;
  BERTScore?: number;
  bert_score?: number;
  [key: string]: any;
}

export interface ModelStats {
  n_examples?: number;
  n_errors?: number;
  n_successful?: number;
  api_success_rate?: number;
  semantic_matches?: number;
  semantic_match_rate?: number;
  avg_semantic_confidence?: number;
  semantic_matching_enabled?: boolean;
  [key: string]: any;
}

export interface ModelResultItem {
  scores: ModelScores;
  stats: ModelStats;
  report?: any;
  error?: string;
  error_type?: string;
}

export interface BenchmarkResults {
  success: boolean;
  model_results: Record<string, ModelResultItem>;
  stats: {
    n_models: number;
    models: string[];
    semantic_matching_enabled: boolean;
  };
  excel_path?: string;
  detailed_samples_path?: string;
  comparison_excel_path?: string;
  error?: string;
}

export interface LeaderboardEntry {
  Model: string;
  Total?: number;
  Combined_Score?: number;
  Accuracy?: number;
  F1?: number;
  Precision?: number;
  Recall?: number;
  ROC_AUC?: number;
  ROUGE1?: number;
  ROUGEL?: number;
  BLEU?: number;
  METEOR?: number;
  BERTScore_F1?: number;
  Sem_Match?: number;
  [key: string]: any;
}
