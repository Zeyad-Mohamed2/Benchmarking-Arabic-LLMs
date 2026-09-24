# Arabic LLMs Benchmarking Project 

This project provides a comprehensive benchmarking framework for evaluating Arabic Language Models (LLMs) across multiple natural language processing tasks. The framework assesses model performance on question answering, text summarization, and sarcasm detection tasks using standardized Arabic datasets.

It features a modernized React/Vite frontend matching Hugging Face Spaces styling, communicating dynamically with a high-performance Python FastAPI backend.

## Features

- **Multi-Model Comparison**: Evaluate and compare up to 3 models sequentially with side-by-side results.
- Multi-task evaluation framework
- Automated benchmarking pipeline
- Excel report generation (Summary & Detailed)
- Support for multiple LLM providers through OpenRouter
- Standardized evaluation metrics
- Easy-to-use configuration system

## Multi-Model Benchmarking

The application allows users to select 1 to 3 models for a single benchmark run, enabling direct performance comparison.

### Workflow
1. **Selection**: Choose up to 3 models from the sidebar (supports both preset and custom models).
2. **Execution**: The orchestrator runs the benchmark for each model sequentially to respect API rate limits.
3. **Analysis**:
   - **Visual Comparison**: View individual model performance in dedicated tabs and a summary comparison table.
   - **Unified Reporting**:
     - **Comparison Summary**: Download a side-by-side comparison of key metrics (Accuracy, ROUGE, etc.) in Excel format.
     - **Detailed Samples**: Download a single Excel file containing all input/output samples from all models, labeled by model name for easy filtering.

## Project Structure

```
src/
├── benchmark_arabic_llms/
    ├── app/                # Web application and benchmark orchestration
        └── benchmark_orchestrator.py
    ├── config/            # Configuration files
        ├── benchmark_config.py
        └── data_paths.py
    ├── core/             # Core functionality and enums
        ├── enums.py
        └── exceptions.py
    ├── data/             # Data processing utilities
        ├── data_loader.py
        └── data_preprocessor.py
    ├── evaluation/       # Task-specific evaluators
        ├── benchmark_runner.py
        ├── evaluator.py
        ├── logger.py
        ├── prompt_builder.py
        ├── qa.py
        ├── sarcasm.py
        ├── semantic_matcher.py
        └── summarization.py
    ├── prompts/          # Task-specific prompt templates
        ├── qa.prompt.md
        ├── sarcasm.prompt.md
        └── summarization.prompt.md
    └── services/         # Core services
        ├── excel_exporter.py
        ├── llm_client.py
        └── report_service.py

reports/               # Auto-generated reports and archives
├── excel_results/     # Excel summary files
└── json_reports/      # JSON detailed reports

logs/                  # Logs of benchmark runs
```

## Implementation Notes

### Model Access and API Usage

While our initial plan was to run evaluations using locally hosted Arabic language models, resource constraints led us to adopt a different approach:

- **OpenRouter API Integration**: We utilize the OpenRouter API to access various Arabic-capable language models, which eliminates the need for significant local computational resources.
- **API Rate Limiting**: The use of API services comes with certain limitations:
  - Restricted number of requests per minute
  - Maximum tokens per request
  - Daily/monthly API usage quotas

### Batch Processing Limitations

Due to API constraints, we had to make some adjustments to our evaluation approach:

- **Sample Size**: Instead of processing large batches of test data, we work with carefully selected samples that represent diverse cases for each task.
- **Sequential Processing**: API rate limits necessitate sequential processing of examples rather than parallel batch processing.
- **Cost Optimization**: The implementation includes measures to optimize API usage and manage costs while maintaining meaningful evaluation results.

## Datasets

The project uses the following Arabic datasets for benchmarking:

1. **Question Answering**
   - Source: [sadeem-ai/arabic-qna](https://huggingface.co/datasets/sadeem-ai/arabic-qna) (mirrored locally as `data/sadeem_arabic_qa.csv`, containing `title,text,source,question,answer,has_answer`)
   - Benchmark input schema: `text, question, answer`
   - Note: The default benchmark sample `data/qa_sample.csv` is generated from `data/sadeem_arabic_qa.csv` by filtering rows where `has_answer` is true, and keeping only `text, question, answer`.

2. **Text Summarization**
   - Source: [Arabic Text Summarization Dataset](https://huggingface.co/datasets/abdalrahmanshahrour/ArabicTextSummarization)
   - Task: Text Summarization
   - Size: 8380

3. **Sarcasm Detection**
   - Source: [Arabic Sarcasm Dataset](https://huggingface.co/datasets/iabufarha/ar_sarcasm)
   - Task: Sarcasm Classification
   - Size: 8440

## Evaluation metrics

This project computes and reports task-specific evaluation metrics. The code paths where each metric is calculated are noted so you can find the implementation in the repository.

- Summarization
   - ROUGE-1 (rouge1): Measures unigram (word-level) overlap between the generated summary and the reference. It reports precision/recall/f-measure; we expose the F-measure as a single-score indication of content overlap. Implemented using `rouge_score.RougeScorer` in `src/benchmark_arabic_llms/evaluation/summarization.py`.
   - ROUGE-L (rougeL): Measures the longest common subsequence (LCS) between prediction and reference; useful to capture fluency and ordering. Implemented with `rouge_score.RougeScorer` in the same module.
   - BLEU (bleu): A precision-oriented metric that measures n-gram overlap (with brevity penalty). Computed via the `evaluate` library in `src/benchmark_arabic_llms/evaluation/summarization.py`.
   - METEOR (meteor): A metric that considers synonymy and stem matches (and usually gives better correlation on some summarization tasks). Also computed with the `evaluate` library in `src/benchmark_arabic_llms/evaluation/summarization.py`.

- Question Answering (QA)
   - Accuracy (accuracy): Fraction of correct answers using normalized exact match. Computed in `src/benchmark_arabic_llms/evaluation/qa.py`.
   - F1 score (f1): Average token-overlap F1 between prediction and reference (SQuAD-style). Computed in `src/benchmark_arabic_llms/evaluation/qa.py`.
   - Exact Match (EM): Fraction of predictions that exactly match the reference answer (string equality after normalization). Used as a strict correctness measure. Computed in `src/benchmark_arabic_llms/evaluation/qa.py` and shown in the UI (Exact Match).
   - ROUGE-L (ROUGE): In QA we also compute a ROUGE-L F-measure between prediction and reference to provide a softer match score when answers are partially correct. See `src/benchmark_arabic_llms/evaluation/qa.py`.
   - Semantic matching (optional): When enabled, the app can use a semantic matcher (Gemini) to judge similarity rather than exact string match. This produces a match flag and a confidence score and is wired through `src/benchmark_arabic_llms/evaluation/llm_judge.py` and the Streamlit UI toggle in `src/benchmark_arabic_llms/app/streamlit_benchmark_app.py`.

- Sarcasm Detection
   - Accuracy (accuracy): Fraction of correct class predictions. Implemented using `sklearn.metrics.accuracy_score` in `src/benchmark_arabic_llms/evaluation/sarcasm.py`.
   - F1 score (f1): Harmonic mean of precision and recall; useful when classes are imbalanced. Computed with `sklearn.metrics.f1_score` in `src/benchmark_arabic_llms/evaluation/sarcasm.py`.
   - Recall (recall): Fraction of true positives detected among all actual positives. Computed with `sklearn.metrics.recall_score` in `src/benchmark_arabic_llms/evaluation/sarcasm.py`.
   - ROC AUC (roc_auc): Area under the ROC curve; measures ranking ability of model scores for binary classification. Computed with `sklearn.metrics.roc_auc_score` in `src/benchmark_arabic_llms/evaluation/sarcasm.py` (when probability or score outputs are available).

Notes on interpretation
- ROUGE/BLEU/METEOR: These are automatic textual overlap metrics. They are useful for fast, repeatable comparisons but have known limitations (e.g., they may penalize valid paraphrases). Use them together rather than relying on a single metric.
- Exact Match vs. Semantic Matching: EM is strict and desirable for factoid QA where wording is consistent; semantic matching is more permissive and can better reflect answer equivalence in Arabic when synonyms or paraphrasing are common.
- Classification metrics (accuracy/F1/ROC AUC): For sarcasm detection, prefer F1 (or class-balanced F1) when the dataset is imbalanced. ROC AUC is helpful when the model returns scores or probabilities instead of hard labels.

## Requirements

- Python 3.10+
- Node.js & npm (for the React Frontend)
- Poetry (for dependency management)
- Required Python packages (installed automatically via Poetry):
  - fastapi
  - uvicorn
  - streamlit
  - evaluate
  - rouge-score
  - scikit-learn
  - python-dotenv
  - openpyxl
  - pandas
  - tqdm

## Setup And Usage

### 1. Installation
First, install the Python backend dependencies using Poetry, and then install the Node.js frontend dependencies:

```bash
# Install Python dependencies
poetry install

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Variables
Create a `.env` file in the root directory based on `.env.example` (if it exists) and add your keys:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Running the Application (Full Stack UI)
You can run both the FastAPI backend and the React frontend simultaneously with a single command:

```bash
poetry run python start.py
```
This will start the backend on port `8000` and the frontend on port `5173`. Open `http://localhost:5173` in your browser.

### 4. Running the Legacy UI (Optionally)
If you prefer to run the legacy Streamlit interface, you can still trigger it natively:

```bash
poetry run python src/benchmark_arabic_llms/main.py --mode ui
```

1. Clone the repository:
```bash
git clone <repository-url>
cd benchmark-arabic-llms
```

2. Install dependencies:
```bash
poetry install
```

## Usage Guide

### Starting the Application

1. Launch the benchmarking application:
```bash
poetry run streamlit run src/benchmark_arabic_llms/main.py
```

### Interface Overview

The application provides a web interface with the following sections:

#### 1. Sidebar Configuration
- **Task Selection**:
  - Choose from available benchmark tasks (QA, Summarization, Sarcasm Detection)
  - Select one task at a time
  
- **Model Selection**:
  - Choose from predefined models or enter a custom model identifier
  - Available models include:
    - google/gemma-3-27b-it
    - qwen/qwen3-4b
    - cohere/command-r7b-12-2024
    - meta-llama/llama-3.3-70b-instruct
  
- **Sample Size**:
  - Set the number of samples to evaluate
  - Minimum value: 1
  - Use smaller numbers for testing

- **Semantic Matching**:
  - Toggle semantic matching using Gemini
  - Requires GEMINI_API_KEY in .env file
  - Provides more flexible answer evaluation

#### 2. Main Interface

##### Prompt Configuration
- **Custom Prompt Option**:
  - Toggle between default and custom prompts
  - Text area for entering custom prompt template
  - Use placeholders like {text}, {question}

##### Benchmark Status
- Shows current configuration:
  - Selected task
  - Number of samples
  - Matching method (Semantic/Exact)

##### Results Display
When benchmark completes, results are shown in tabs:

1. **Summary Tab**:
   - Overview of benchmark results
   
2. **Semantic Analysis Tab** (if semantic matching enabled):
   - Detailed semantic comparison results
   
3. **Detailed Scores Tab**:
   - Complete scoring information
   
4. **Statistics Tab**:
   - Processing and performance statistics

### Running a Benchmark

1. **Configuration**:
   - Select your desired task
   - Choose a model
   - Set number of samples
   - (Optional) Enable semantic matching
   - (Optional) Configure custom prompt

2. **Execution**:
   - Click "Run Evaluation" button
   - Wait for completion
   - Review results in the tabs

3. **Results**:
   - Review in-app results
   - Check generated files:
     - JSON report in `reports/[task]_last_run_archive.json`
     - Excel report in `reports/excel_results/[task]_results.xlsx`

## Environment Variables

Create a `.env` file in the project root with the following keys:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here # optional for semantic matching
```

You can obtain an OpenRouter API key from [https://openrouter.ai](https://openrouter.ai)
and a Gemini API key from [https://ai.google.dev/](https://ai.google.dev/).

### Example JSON Output

```json
{
  "task": "question_answering",
   "dataset": "data/qa_sample.csv",
  "model": "google/gemma-3-27b-it",
  "scores": {
      "accuracy": 0.72,
      "f1": 0.74,
      "EM": 0.72,
      "ROUGE": 0.65
  },
  "n_examples": 10,
  "success_rate": 100.0
}
```

### Environment Setup

Before running, ensure:
1. OpenRouter API key is set in `.env` file as `OPENROUTER_API_KEY`
2. (Optional) Gemini API key is set as `GEMINI_API_KEY` if using semantic matching

## Results

Results are automatically generated and stored in multiple formats:

### JSON Reports
- Located in the `reports/` directory
- Task-specific files (e.g., `sarcasm_last_run_archive.json`, `qa_last_run_archive.json`)
- Contains detailed results from the most recent benchmark run
- Includes model responses, evaluation metrics, and timing information

### Excel Reports
- Located in `reports/excel_results/` directory
- Task-specific spreadsheets (e.g., `sarcasm_results.xlsx`, `qa_results.xlsx`)
- Each run is automatically appended as a new row
- Enables easy comparison across different runs and model configurations
- Includes all evaluation metrics and aggregate statistics

### Benchmark Flow

```
Dataset → Preprocessing → Prompt Template → LLM (via OpenRouter)
→ Evaluation (ROUGE/BLEU/EM/F1) → Reports (JSON + Excel)
```

## Logging

All benchmark logs and intermediate model responses are stored in the `logs/` directory.  
Each run is timestamped for traceability. You can review raw model outputs and errors here.

## Troubleshooting

- **Error: GEMINI_API_KEY not found**  
  → Add your Gemini key to the `.env` file.

- **API rate limit exceeded**  
  → Reduce the number of samples or switch to smaller models.

- **Empty Excel report**  
  → Check that the evaluation completed successfully and that write permissions are granted to the `reports/excel_results` directory.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Extending the Framework

You can easily add new Arabic NLP tasks:

1. **Add a new task enum**  
   Update `src/benchmark_arabic_llms/core/enums.py` with a new `BenchmarkTask`.

2. **Add a dataset and prompt template**  
   Place your dataset in `data/` and create a `.prompt.md` in `prompts/`.

3. **Create an evaluator**  
   Implement metric logic in a new file inside `src/benchmark_arabic_llms/evaluation/`.

4. **Update the app**  
   Ensure your new task appears in the `BenchmarkTask.get_all()` list for Streamlit UI selection.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

