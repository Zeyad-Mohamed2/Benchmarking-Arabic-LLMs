# Arabic LLMs Benchmarking Framework

An enterprise-grade, open-source benchmarking and evaluation framework for assessing Arabic Large Language Models (LLMs) across diverse Natural Language Processing tasks.

The framework pairs a high-performance **Python FastAPI backend** with a modern **React 19 + TypeScript + Vite frontend** tailored with Hugging Face Spaces aesthetics. It features multi-model simultaneous benchmarking, Groq LPU hardware acceleration, Gemini-powered semantic evaluation, fault-tolerant checkpoint resumption, qualitative side-by-side prompt inspection, and publication-quality reporting (Executive Excel, Standalone HTML, and 1-Click PDF exports).

---

## 🌟 Key Features

### 1. Interactive Model Catalog & Multi-Model Comparison
- **Evaluate Up to 3 Models Simultaneously:** Compare architectures, parameter sizes, and provider outputs sequentially to respect API rate limits.
- **"Browse Models" Modal Popup:**
  - Full-text search by model name, slug, or capability tag.
  - Quick filter chips: **Free Tier Only**, parameter size filters (**<10B**, **10B–30B**, **>50B**), and provider filters (**OpenRouter**, **Groq**).
  - **1-Click Comparison Presets:**
    - ⚡ *Free Arabic Trio* (Gemma 3 27B, Llama 3.3 70B, Qwen 2.5 7B)
    - 🧠 *70B+ Giants* (Llama 3.3 70B, Qwen 2.5 72B)
    - 🏎️ *Ultra-Fast Groq LPUs* (Llama 3.3 70B on sub-second Groq hardware)
  - **Pluggable Custom Models:** Add and persist custom model slugs with metadata directly in browser `localStorage`.
- **Dual LLM Provider Support:** Access models via [OpenRouter](https://openrouter.ai) or high-throughput [Groq](https://groq.com) LPUs.
- **Configurable Gemini Semantic Evaluator:** Choose between `gemini-2.5-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-pro`, or custom judge models.

### 2. Qualitative Side-by-Side Sample Inspector
- **Prompt-by-Prompt Deep Dive:** Inspect individual Arabic examples ($1 \dots N$) with previous/next controls, jump selectors, and match filters (**All**, **✅ Matches Only**, **❌ Mismatches Only**).
- **Arabic RTL Typography:** Native Right-to-Left styling for input contexts, questions, references, and model outputs.
- **Ground Truth Target Standard:** Highlighted target reference with 1-click copy.
- **Side-by-Side Model Predictions:** Comparative cards showing model predictions, evaluation badges (`✅ Exact Match`, `🧠 Semantic Match (Conf: XX%)`, `❌ Mismatch`), and expandable **LLM Judge Reasoning** explaining why answers were accepted or penalized.

### 3. Executive Publication-Quality Reporting
- **Executive Excel Workbooks (`.xlsx`):**
  - Styled with corporate/academic aesthetics (deep navy `#0F172A` headers, `#32C4B7` teal accents, alternating zebra striping).
  - Auto-fitted column widths and scientific number formatting (`0.0000`, `0.0%`).
  - **Conditional Formatting Heatmaps:** Smooth color gradients (soft red $\rightarrow$ yellow $\rightarrow$ soft green) applied to score columns.
  - **Executive Summary Sheet:** KPI cards (🏆 Top Model, 🎯 Best Score, ⚡ Success Rate, 📊 Total Samples) and embedded native Excel bar charts.
- **Standalone Interactive HTML Reports (`.html`):**
  - Self-contained, offline-compatible HTML report with embedded CSS, metric scorecards, comparative breakdown tables, and an interactive pure SVG multi-model radar chart.
  - **1-Click PDF Export:** Pre-configured `@media print` styling allowing users to print or save publication-ready PDF reports directly from the browser.
- **Detailed Samples Spreadsheet (`.xlsx`):** Every evaluated sample logged with prompt context, question, expected output, model generation, match status, and judge feedback.

### 4. Fault-Tolerant Checkpoint & Resume Mode
- Configurable checkpoint intervals (e.g., save state every 10, 25, or 50 samples).
- Automatically saves state to `.jsonl` and checkpoint files.
- Resumes seamlessly from the exact failure point if an API rate limit, quota exhaustion, or network disconnect occurs.

### 5. Live Task Leaderboard
- Persistent task leaderboards tracking top-performing Arabic models across Question Answering, Summarization, and Sarcasm Detection.
- 1-click model promotion directly from benchmark runs into the global leaderboard.

---

## 📁 Project Structure

```
benchmarking-arabic-llms/
├── data/                                 # Standardized benchmark datasets
│   ├── qa_sample.csv                     # Arabic Question Answering dataset
│   ├── summarization_sample.csv          # Arabic Text Summarization dataset
│   ├── sarcasm_sample.csv                # Arabic Sarcasm Detection dataset
│   └── leaderboard/                      # CSV leaderboard stores per task
├── frontend/                             # React 19 + Vite + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── benchmark/                # Results viewer, SampleInspector, progress bars
│   │   │   ├── charts/                   # Multi-model SVG radar charts
│   │   │   ├── layout/                   # Header, task tabs
│   │   │   ├── modals/                   # BrowseModelsModal (portal dialog)
│   │   │   └── sidebar/                  # ConfigSidebar (parameters, providers, API keys)
│   │   ├── data/                         # Model catalog definitions & presets
│   │   ├── services/                     # FastAPI client, SSE event streams
│   │   └── types/                        # TypeScript interfaces and schemas
│   ├── package.json                      # Frontend dependencies and scripts
│   └── vite.config.ts                    # Vite configuration
├── src/
│   └── benchmark_arabic_llms/            # Core Python package
│       ├── api/                          # FastAPI REST API & SSE streaming routes
│       │   ├── main.py                   # FastAPI app entry point
│       │   └── routes/                   # Benchmark, download, samples, and leaderboard routes
│       ├── app/                          # Orchestration & legacy Streamlit app
│       │   ├── benchmark_orchestrator.py # Multi-model run execution & checkpoint manager
│       │   └── streamlit_benchmark_app.py# Streamlit interface
│       ├── config/                       # Configuration schemas & data paths
│       ├── core/                         # Task enums and domain exceptions
│       ├── data/                         # Data loaders and text preprocessors
│       ├── evaluation/                   # Task evaluators & metric engines
│       │   ├── benchmark_runner.py       # Example processing runner with retry logic
│       │   ├── evaluator.py              # Central metric dispatcher
│       │   ├── qa.py                     # QA metrics (EM, F1, Accuracy, ROUGE-L)
│       │   ├── summarization.py          # Summarization metrics (ROUGE-1/L, BLEU, METEOR)
│       │   ├── sarcasm.py                # Sarcasm metrics (Accuracy, F1, Precision, Recall, AUC)
│       │   └── semantic_matcher.py       # Gemini-based LLM semantic judge
│       ├── prompts/                      # Task prompt templates (Markdown format)
│       ├── reporting/                    # Executive report generation modules
│       │   ├── excel_styler.py           # OpenPyXL executive workbook styler & heatmaps
│       │   └── html_report.py            # Standalone HTML report & print-to-PDF generator
│       └── services/                     # LLM clients, Excel export, and report service
├── tests/                                # Automated test suite (Pytest)
│   ├── integration/                      # End-to-end pipeline tests
│   └── unit/                             # Metrics, normalization, and task registry tests
├── reports/                              # Output directory for Excel, HTML, and JSON reports
├── logs/                                 # Runtime logs and detailed sample JSONL files
├── pyproject.toml                        # Poetry project configuration & dependencies
├── start.py                              # Unified full-stack launch script
└── README.md                             # Project documentation
```

---

## 📊 Datasets & Evaluation Metrics

### Datasets
| Task | Dataset Source | Input Fields | Ground Truth |
|---|---|---|---|
| **Question Answering** | [sadeem-ai/arabic-qna](https://huggingface.co/datasets/sadeem-ai/arabic-qna) | `text` (context), `question` | `answer` |
| **Text Summarization** | [Arabic Text Summarization](https://huggingface.co/datasets/abdalrahmanshahrour/ArabicTextSummarization) | `text` (article) | `summary` |
| **Sarcasm Detection** | [Arabic Sarcasm Dataset](https://huggingface.co/datasets/iabufarha/ar_sarcasm) | `text` (tweet/phrase) | `label` (`ساخر` / `غير ساخر`) |

### Evaluation Metrics
- **Summarization:**
  - **ROUGE-1 & ROUGE-L:** Unigram and Longest Common Subsequence overlap via `rouge-score`.
  - **BLEU:** Precision-oriented n-gram overlap with brevity penalty via `sacrebleu`.
  - **METEOR:** Alignment-based metric accounting for stemming and synonymy via `evaluate`/`nltk`.
- **Question Answering:**
  - **Exact Match (EM):** Strict string match after Arabic diacritic and orthographic normalization.
  - **Token F1:** Word-level harmonic overlap between predicted answer and reference.
  - **Accuracy & ROUGE-L:** Answer-level classification and fluency overlap.
  - **Semantic Match (Gemini Judge):** Flexible semantic equivalence evaluation with confidence scoring (`0.0` to `1.0`) and explanatory rationale.
- **Sarcasm Detection:**
  - **Accuracy & Macro F1:** Classification accuracy and class-balanced harmonic mean via `scikit-learn`.
  - **Precision & Recall:** False positive / false negative balance.
  - **ROC-AUC:** Area under ROC curve for class discrimination.

---

## 💻 Prerequisites

Ensure you have the following installed on your machine:
- **Python:** `3.11` or higher (Python `3.12` / `3.13` / `3.14` supported; note: `3.14.1` has a known upstream bug, use `3.14.0` or `3.14.2+`).
- **Poetry:** For Python dependency and virtual environment management ([Install Poetry](https://python-poetry.org/docs/#installation)).
- **Node.js & npm:** Node.js `18.x` or higher and npm `9.x` or higher ([Download Node.js](https://nodejs.org/)).
- **API Keys:**
  - **OpenRouter API Key:** From [openrouter.ai](https://openrouter.ai/) (required for OpenRouter models).
  - **Groq API Key:** From [console.groq.com](https://console.groq.com/) (optional, for ultra-fast Groq LPU models).
  - **Gemini API Key:** From [ai.google.dev](https://ai.google.dev/) (optional, required when enabling LLM Semantic Matching).

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Zeyad-Mohamed2/Benchmarking-Arabic-LLMs.git
cd Benchmarking-Arabic-LLMs
```

### 2. Install Python Backend Dependencies
Install all required Python dependencies into an isolated virtual environment via Poetry:
```bash
poetry install
```

### 3. Install Frontend Dependencies
Navigate to the `frontend` directory and install the Node.js packages:
```bash
cd frontend
npm install
cd ..
```

### 4. Configure Environment Variables
Copy the example environment template and populate your API credentials:
```bash
cp .env.example .env
```
Edit `.env` with your preferred text editor:
```ini
# Primary Provider API Keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional: Semantic Matcher LLM Judge
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🛠️ Build & Verification Commands

### 1. Build and Type-Check the Frontend
Validate TypeScript types and build the production bundle:
```bash
npm --prefix frontend run build
```
*(Alternative from inside `frontend/`: `npm run build`)*

### 2. Run Backend Unit & Integration Tests
Execute the comprehensive test suite (15 unit and integration tests covering normalization, tasks, metrics, and end-to-end pipelines):
```bash
poetry run pytest -v
```

To run specific test categories:
```bash
# Unit tests only
poetry run pytest tests/unit/ -v

# Integration tests only
poetry run pytest tests/integration/ -v
```

---

## 🏃 Running the Application

### Option A: Unified Full-Stack Launch (Recommended)
Launch both the **FastAPI backend** (port `8000`) and the **Vite React frontend** (port `5173`) with a single command:
```bash
poetry run python start.py
```
- **Web Application:** Open [http://localhost:5173](http://localhost:5173) in your browser.
- **FastAPI Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs).
- Press `Ctrl + C` in the terminal to gracefully terminate both servers.

---

### Option B: Running Services Independently

#### Terminal 1 — FastAPI Backend:
```bash
poetry run python src/benchmark_arabic_llms/main.py --mode api --port 8000
```
*(Or directly with Uvicorn: `poetry run uvicorn benchmark_arabic_llms.api.main:app --host 0.0.0.0 --port 8000 --reload`)*

#### Terminal 2 — React Vite Frontend:
```bash
npm --prefix frontend run dev
```
*(Or inside `frontend/`: `npm run dev`)*

---

### Option C: Legacy Streamlit UI
If you need to access the legacy Streamlit interface:
```bash
poetry run python src/benchmark_arabic_llms/main.py --mode ui
```
The Streamlit app will start at [http://localhost:8501](http://localhost:8501).

---

## 📖 How to Run a Benchmark

1. **Select Task:** Choose between **Question Answering**, **Text Summarization**, or **Sarcasm Detection** in the sidebar.
2. **Select Provider & API Key:** Choose **OpenRouter** or **Groq** and provide your API key (automatically loaded if configured in `.env`).
3. **Browse & Select Models:**
   - Click **`🔍 Browse & Select Models`** to open the interactive modal catalog.
   - Pick a 1-click comparison preset or select up to 3 individual models.
   - Use the **`➕ Plug Custom Model`** tab to enter any new model slug not currently in the catalog.
4. **Configure Samples & Features:**
   - Set **Sample Size** (start with 5–10 samples for quick testing).
   - Toggle **Semantic Matching (Gemini)** if you wish to evaluate answers via an LLM judge.
   - Toggle **Checkpoint Mode** if evaluating large sample batches to guard against timeouts.
5. **Run Evaluation:**
   - Click **`Test Connection`** to ensure your API keys and models are reachable.
   - Click **`Run Benchmark`** to begin streaming progress in real-time.
6. **Inspect & Export:**
   - **Sample Inspector:** Inspect question-by-question Arabic outputs and judge feedback in the **`🔍 Sample Inspector`** tab.
   - **Radar Analysis:** Compare multidimensional metric footprints in the **`🕸️ Radar Analysis`** tab.
   - **Executive Exports:** Download publication-ready Excel workbooks, standalone HTML reports, or 1-click PDF documents from the top toolbar.
   - **Promote to Leaderboard:** Click **`Add to Leaderboard`** on any model run to update the global task leaderboard.

---

## 🔧 Troubleshooting & FAQs

- **Q: Model selection modal was hidden under the header.**  
  *A:* This has been fixed in the latest version using React Portals (`createPortal(..., document.body)`) with elevated `z-[9999]`.
- **Q: EventSource "Connection lost to benchmark server" on completion.**  
  *A:* The SSE stream listener gracefully closes upon receiving the `done` event payload, preventing unneeded reconnections after benchmark termination.
- **Q: Rate Limit (`429`) errors from providers.**  
  *A:* Free-tier models on OpenRouter and Groq have per-minute request limits. Enable **Checkpoint Mode** with an interval of 10–25 samples. If interrupted, restarting the benchmark with the same parameters will resume progress from where it stopped.
- **Q: Port 8000 or 5173 is already in use.**  
  *A:* You can customize the backend port by passing `--port <PORT>`:
  ```bash
  poetry run python src/benchmark_arabic_llms/main.py --mode api --port 8080
  ```
  And specify a custom port for Vite in `frontend/vite.config.ts`.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
