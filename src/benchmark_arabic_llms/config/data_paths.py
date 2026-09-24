"""
This file defines and initializes all directory and file paths used across the benchmark project.
It sets up locations for datasets, prompts, logs, and reports, ensuring required folders exist at runtime.
"""
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[3]

DATA_DIR = ROOT_PATH / "data"
PROMPTS_DIR = ROOT_PATH / "src" / "benchmark_arabic_llms" / "prompts"
LOGS_DIR = ROOT_PATH / "logs"

# Dataset paths
SUMMARIZATION_DATA_CSV = DATA_DIR / "summarization_sample.csv"
QA_DATA_CSV = DATA_DIR / "qa_sample.csv"
SARCASM_DATA_CSV = DATA_DIR / "sarcasm_sample.csv"

# Prompt template paths
SUMMARIZATION_PROMPT = PROMPTS_DIR / "summarization.prompt.md"
QA_PROMPT = PROMPTS_DIR / "qa.prompt.md"
SARCASM_PROMPT = PROMPTS_DIR / "sarcasm.prompt.md"

# Judge prompt template paths
QA_JUDGE_PROMPT = PROMPTS_DIR / "qa_judge.prompt.md"
SARCASM_JUDGE_PROMPT = PROMPTS_DIR / "sarcasm_judge.prompt.md"
SUMMARIZATION_JUDGE_PROMPT = PROMPTS_DIR / "summarization_judge.prompt.md"

# Output paths
REPORTS_DIR = ROOT_PATH / "reports"
SUMMARIZATION_REPORT_PATH = REPORTS_DIR / "summarization_last_run_archive.json"
QA_REPORT_PATH = REPORTS_DIR / "qa_last_run_archive.json"
SARCASM_REPORT_PATH = REPORTS_DIR / "sarcasm_last_run_archive.json"
EXCEL_DIR = REPORTS_DIR / "excel_results"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
EXCEL_DIR.mkdir(parents=True, exist_ok=True)
