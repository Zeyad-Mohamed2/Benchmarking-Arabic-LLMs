"""
This file defines the BenchmarkOrchestrator, which manages the full benchmarking workflow.
It coordinates data loading, model evaluation, semantic matching, and report generation with optional progress tracking.
"""

import base64
import json
import os
import zlib
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
from benchmark_arabic_llms.core.enums import BenchmarkTask
from benchmark_arabic_llms.services.llm_client import ClientFactory
from benchmark_arabic_llms.services.report_service import ReportService
from benchmark_arabic_llms.config.benchmark_config import ConfigManager
from benchmark_arabic_llms.data.data_preprocessor import preprocess_records
from benchmark_arabic_llms.evaluation.llm_judge import SemanticMatcher
from benchmark_arabic_llms.evaluation.benchmark_runner import BenchmarkRunner
from benchmark_arabic_llms.data.data_loader import DataLoader, PromptTemplateLoader
from benchmark_arabic_llms.core.exceptions import (
    ClientError,
    RateLimitError,
    PaymentError,
    TokenLimitError,
    TimeoutError,
)


class BenchmarkOrchestrator:
    """Orchestrates the entire benchmark workflow."""

    def __init__(self, log_dir: Path, excel_dir: Path):
        self.data_loader = DataLoader()
        self.template_loader = PromptTemplateLoader()
        self.log_dir = log_dir
        self.report_service = ReportService(excel_dir)

    def run_multiple(
        self,
        task: BenchmarkTask,
        model_names: List[str],
        api_key: str,
        provider: str = "openrouter",
        custom_prompt: Optional[str] = None,
        number_of_samples: int = 10,
        gemini_api_key: Optional[str] = None,
        gemini_model_name: Optional[str] = None,
        use_semantic_matching: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        uploaded_dataset: Optional[Any] = None,
        enable_checkpoint_mode: bool = False,
        checkpoint_interval: int = 50,
    ) -> Dict[str, Any]:
        """Run benchmark workflow for multiple models sequentially.

        Args:
            task: The benchmark task to run
            model_names: List of model names to benchmark (up to 5)
            api_key: API key for the selected provider
            provider: Model provider ("openrouter" or "groq")
            custom_prompt: Optional custom prompt template
            number_of_samples: Number of samples to process
            gemini_api_key: Optional Gemini API key for semantic matching
            gemini_model_name: Optional Gemini model name for semantic matching
            use_semantic_matching: Whether to use semantic matching
            progress_callback: Optional callback function with signature:
                (current: int, total: int, status: str) -> None
            uploaded_dataset: Streamlit UploadedFile object containing custom dataset
            enable_checkpoint_mode: Enable checkpoint/resume functionality
            checkpoint_interval: Save checkpoint every N samples
        """
        try:
            fast_resume_mode = os.getenv("BENCHMARK_FAST_RESUME", "1") == "1"
            compress_checkpoints = os.getenv("BENCHMARK_COMPRESS_CHECKPOINTS", "1") == "1"

            # Validate model count
            if not model_names or len(model_names) > 5:
                return {"success": False, "error": "Please select 1-5 models"}

            # Ensure task is a BenchmarkTask enum
            if isinstance(task, str):
                task = BenchmarkTask(task)
            task_str = task.value

            # Report stage: Configuration
            if progress_callback:
                progress_callback(
                    0, 100, f"Loading configuration for {len(model_names)} model(s)..."
                )

            # Load configuration once
            config = ConfigManager.create(task_str)

            # Create semantic matcher if enabled (once for all models)
            semantic_matcher = None
            if use_semantic_matching and gemini_api_key:
                try:
                    model = gemini_model_name or "gemini-2.5-flash-lite"
                    semantic_matcher = SemanticMatcher(gemini_api_key, model)
                    print(f"✓ Semantic matching enabled with Gemini ({model})")
                except Exception as e:
                    print(f"Warning: Could not initialize semantic matcher: {e}")
                    print("Falling back to exact matching")

            # Report stage: Data loading
            if progress_callback:
                progress_callback(5, 100, "Loading dataset...")

            # Load data once (use same data for all models)
            if uploaded_dataset is not None:
                data = self.data_loader.load_uploaded_dataset(
                    uploaded_dataset, task, number_of_samples
                )
            else:
                data = self.data_loader.load_dataset(
                    config.dataset_path, task, number_of_samples
                )

            data = preprocess_records(data)

            # Load prompt template
            prompt_template = (
                custom_prompt
                if custom_prompt
                else self.template_loader.load(config.prompt_template_path)
            )

            # Report stage: Data loading complete
            if progress_callback:
                progress_callback(20, 100, "Data loaded. Starting processing...")

            # ONLY check for run checkpoint if checkpoint mode is enabled
            models_state = []
            start_model_index = 0
            run_checkpoint = None
            
            if enable_checkpoint_mode:
                run_checkpoint_path = self._get_run_checkpoint_path(task_str)
                if run_checkpoint_path.exists():
                    run_checkpoint = self._load_run_checkpoint(run_checkpoint_path)
                    if run_checkpoint:
                        print(f"📍 Found incomplete run from {run_checkpoint.get('run_timestamp', 'unknown')}")
                        models_state = run_checkpoint.get('models_queue', [])
                        start_model_index = run_checkpoint.get('current_model_index', 0)
                        
                        # Verify models match
                        checkpoint_models = [m['model_name'] for m in models_state]
                        if checkpoint_models != model_names:
                            print(f"⚠️ Model list changed, starting fresh run")
                            models_state = []
                            start_model_index = 0
                        else:
                            completed = [m['model_name'] for m in models_state if m['status'] == 'completed']
                            if completed:
                                print(f"   ✓ Completed: {', '.join(completed)}")
                            print(f"   🔄 Resuming from model {start_model_index + 1}/{len(model_names)}")
            
            # Initialize models state if not loaded from checkpoint
            if not models_state:
                models_state = [
                    {"model_name": name, "status": "pending", "results": None}
                    for name in model_names
                ]

            # Run evaluation for each model sequentially
            model_results = {}
            
            # Load results for already-completed models BEFORE the loop
            if enable_checkpoint_mode and models_state:
                for model_state in models_state:
                    if model_state["status"] == "completed" and model_state.get("results"):
                        model_name = model_state["model_name"]
                        model_results[model_name] = model_state["results"]
                        print(f"✓ Loaded results for completed model: {model_name}")
            
            progress_per_model = 60 / len(
                model_names
            )  # Allocate 60% for processing all models

            for idx in range(start_model_index, len(model_names)):
                model_state = models_state[idx]
                model_name = model_state["model_name"]
                
                # Skip if already completed in this run (results already loaded above)
                if model_state["status"] == "completed":
                    print(f"⏭️ Skipping {model_name} (already completed in this run)")
                    continue

                model_start_progress = 20 + int(idx * progress_per_model)
                model_end_progress = 20 + int((idx + 1) * progress_per_model)

                if progress_callback:
                    progress_callback(
                        model_start_progress,
                        100,
                        f"Processing Model {idx + 1}/{len(model_names)}: {model_name.replace(':free', '')}...",
                    )

                try:
                    # Create client for this model
                    if provider == "groq":
                        client = ClientFactory.create_groq_client(api_key, model_name)
                    else:
                        client = ClientFactory.create_openrouter_client(api_key, model_name)

                    # Get checkpoint data if this model was in progress
                    checkpoint_data = None
                    if model_state["status"] == "in_progress":
                        checkpoint_data = model_state.get("checkpoint_data")
                        if checkpoint_data:
                            last_idx = checkpoint_data.get("last_sample_index", -1)
                            print(f"🔄 Resuming {model_name} from sample {last_idx + 1}/{number_of_samples}")

                    # Create wrapper callback that scales progress for this model
                    def model_progress_callback(current: int, total: int, status: str):
                        if progress_callback:
                            progress_range = model_end_progress - model_start_progress
                            progress_percent = model_start_progress + int(
                                (current / max(total, 1)) * progress_range * 0.9
                            )
                            progress_callback(
                                progress_percent,
                                100,
                                f"{model_name.replace(':free', '')}: {status}",
                            )
                    
                    # Create checkpoint callback for runner to save progress during execution
                    def model_checkpoint_callback(runner_state: Dict):
                        """Called by runner to save checkpoint during model execution."""
                        if enable_checkpoint_mode:
                            models_state[idx] = {
                                "model_name": model_name,
                                "status": "in_progress",
                                "checkpoint_data": runner_state,
                                "results": None
                            }
                            self._save_run_checkpoint(
                                task_str,
                                model_names,
                                models_state,
                                idx,
                                number_of_samples,
                                checkpoint_interval,
                                compress_checkpoints,
                            )

                    # Run Evaluation for this model
                    runner = BenchmarkRunner(
                        client=client,
                        task=task,
                        prompt_template=prompt_template,
                        log_dir=self.log_dir,
                        semantic_matcher=semantic_matcher,
                        progress_callback=model_progress_callback,
                        clear_log=(idx == 0 and checkpoint_data is None),  # Don't clear if resuming
                        enable_checkpoint_mode=enable_checkpoint_mode,
                        checkpoint_interval=checkpoint_interval,
                        checkpoint_data=checkpoint_data,
                        model_name=model_name,
                        checkpoint_callback=model_checkpoint_callback if enable_checkpoint_mode else None,
                        fast_resume_mode=fast_resume_mode,
                    )
                    runner.process_examples(data)

                    # Evaluate results
                    stats = runner.get_stats()
                    scores = runner.evaluate()

                    # Generate report for this model
                    report = self.report_service.generate_and_save_report(
                        config, scores, stats, model_name, runner.get_report_path()
                    )

                    # Store results for this model
                    model_results[model_name] = {
                        "scores": scores,
                        "stats": stats,
                        "report": report,
                    }
                    
                    # Update run checkpoint after each model completes
                    if enable_checkpoint_mode:
                        models_state[idx] = {
                            "model_name": model_name,
                            "status": "completed",
                            "results": model_results[model_name]
                        }
                        self._save_run_checkpoint(
                            task_str,
                            model_names,
                            models_state,
                            idx + 1,
                            number_of_samples,
                            checkpoint_interval,
                            compress_checkpoints,
                        )
                        print(f"💾 Run checkpoint saved (Model {idx + 1}/{len(model_names)} complete)")

                    if progress_callback:
                        progress_callback(
                            model_end_progress,
                            100,
                            f"Completed {model_name.replace(':free', '')}",
                        )

                except Exception as e:
                    # Extract error type for better user feedback
                    error_type = "Error"
                    error_msg = str(e)
                    
                    if isinstance(e, RateLimitError):
                        error_type = "Rate Limit"
                        error_msg = "Too many requests - API rate limit exceeded"
                    elif isinstance(e, PaymentError):
                        error_type = "Payment/Billing"
                        error_msg = "Payment or quota issue - check your account"
                    elif isinstance(e, TokenLimitError):
                        error_type = "Token Limit"
                        error_msg = "Request exceeds token limits"
                    elif isinstance(e, TimeoutError):
                        error_type = "Timeout"
                        error_msg = "Request timed out"
                    elif isinstance(e, ClientError):
                        error_type = e.error_type.replace("_", " ").title()
                        error_msg = str(e)
                    
                    full_error_msg = f"[{error_type}] {error_msg}"
                    
                    print(f"Error processing model {model_name}: {full_error_msg}")
                    if progress_callback:
                        progress_callback(
                            model_end_progress,
                            100,
                            f"Error with {model_name}: {full_error_msg}",
                        )
                    model_results[model_name] = {
                        "error": full_error_msg,
                        "error_type": error_type,
                        "scores": {},
                        "stats": {
                            "error": full_error_msg,
                            "error_type": error_type,
                            "n_examples": number_of_samples,
                            "n_errors": number_of_samples,
                            "api_success_rate": 0.0,
                        },
                    }

            # Check if all models failed
            failed_models = [m for m, r in model_results.items() if "error" in r]
            if len(failed_models) == len(model_names):
                error_details = "\n".join(
                    [f"- {m}: {model_results[m]['error']}" for m in failed_models]
                )
                return {
                    "success": False,
                    "error": f"All models failed to process.\n{error_details}",
                }

            # Report stage: Report generation (75-95%)
            if progress_callback:
                progress_callback(75, 100, "Generating comparison reports...")

            task_str = task.value if isinstance(task, BenchmarkTask) else task

            # Export individual run results
            current_run_excel_path = None
            if model_results and len(model_results) > 0:
                first_model_name = list(model_results.keys())[0]
                first_report = model_results[first_model_name].get("report", {})
                if first_report:
                    current_run_excel_path = self.report_service.export_current_run(
                        first_report, task_str
                    )

            # Export detailed samples
            # For multiple models, we want to export samples for ALL models run in this session
            # Each model processed 'number_of_samples' examples
            total_examples = number_of_samples * len(model_results)
            detailed_samples_path = self.report_service.export_detailed_samples(
                self.log_dir, task_str, total_examples
            )

            # Generate comparison Excel file if multiple models
            comparison_excel_path = None
            if len(model_results) > 1:
                comparison_excel_path = self.report_service.export_model_comparison(
                    model_results, task_str
                )

            # Clear run checkpoint after successful completion
            if enable_checkpoint_mode:
                self._clear_run_checkpoint(task_str)
                print(f"🧹 Run checkpoint cleared (all models completed)")

            # Complete
            if progress_callback:
                progress_callback(100, 100, "Benchmark completed!")

            return {
                "success": True,
                "model_results": model_results,
                "stats": {
                    "n_models": len(model_results),
                    "models": list(model_results.keys()),
                    "semantic_matching_enabled": use_semantic_matching,
                },
                "excel_path": (
                    str(current_run_excel_path) if current_run_excel_path else None
                ),
                "detailed_samples_path": (
                    str(detailed_samples_path) if detailed_samples_path else None
                ),
                "comparison_excel_path": (
                    str(comparison_excel_path) if comparison_excel_path else None
                ),
            }

        except Exception as e:
            # Extract error type for better user feedback
            error_type = "Error"
            error_msg = str(e)
            
            if isinstance(e, RateLimitError):
                error_type = "Rate Limit"
                error_msg = "Too many requests - API rate limit exceeded"
            elif isinstance(e, PaymentError):
                error_type = "Payment/Billing"
                error_msg = "Payment or quota issue - check your account"
            elif isinstance(e, TokenLimitError):
                error_type = "Token Limit"
                error_msg = "Request exceeds token limits"
            elif isinstance(e, TimeoutError):
                error_type = "Timeout"
                error_msg = "Request timed out"
            elif isinstance(e, ClientError):
                error_type = e.error_type.replace("_", " ").title()
                error_msg = str(e)
            
            full_error_msg = f"[{error_type}] {error_msg}"
            
            if progress_callback:
                progress_callback(0, 100, f"Error: {full_error_msg}")
            return {"success": False, "error": full_error_msg, "error_type": error_type}

    def _get_run_checkpoint_path(self, task: str) -> Path:
        """Get run checkpoint file path for the entire benchmark run."""
        return self.log_dir / f"{task}_run_checkpoint.json"

    def _load_run_checkpoint(self, checkpoint_path: Path) -> Optional[Dict]:
        """Load run checkpoint data from file."""
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)

            for model_state in checkpoint_data.get("models_queue", []):
                compressed_data = model_state.pop("checkpoint_data_compressed", None)
                if compressed_data:
                    try:
                        raw = base64.b64decode(compressed_data.encode("ascii"))
                        decoded = zlib.decompress(raw).decode("utf-8")
                        model_state["checkpoint_data"] = json.loads(decoded)
                    except Exception as e:
                        print(f"⚠️ Failed to decode compressed checkpoint data: {e}")
                        model_state["checkpoint_data"] = None

            return checkpoint_data
        except Exception as e:
            print(f"⚠️ Error loading run checkpoint: {e}")
            return None
    
    def _save_run_checkpoint(
        self,
        task: str,
        model_names: List[str],
        models_state: List[Dict],
        current_model_index: int,
        number_of_samples: int,
        checkpoint_interval: int,
        compress_checkpoints: bool = False,
    ) -> None:
        """Save run checkpoint with all models state."""
        from datetime import datetime
        
        checkpoint_path = self._get_run_checkpoint_path(task)
        
        serialized_models_state = []
        for state in models_state:
            state_copy = dict(state)
            if compress_checkpoints and state_copy.get("status") == "in_progress":
                checkpoint_data = state_copy.pop("checkpoint_data", None)
                if checkpoint_data is not None:
                    try:
                        raw = json.dumps(checkpoint_data, ensure_ascii=False).encode("utf-8")
                        compressed = zlib.compress(raw, level=6)
                        state_copy["checkpoint_data_compressed"] = base64.b64encode(compressed).decode("ascii")
                    except Exception as e:
                        print(f"⚠️ Failed to compress checkpoint data: {e}")
                        state_copy["checkpoint_data"] = checkpoint_data
            serialized_models_state.append(state_copy)

        checkpoint_data = {
            "task": task,
            "run_timestamp": datetime.now().isoformat(),
            "number_of_samples": number_of_samples,
            "checkpoint_interval": checkpoint_interval,
            "checkpoint_compression": "zlib+base64" if compress_checkpoints else "none",
            "models_queue": serialized_models_state,
            "current_model_index": current_model_index,
            "total_models": len(model_names),
        }
        
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save run checkpoint: {e}")
    
    def _clear_run_checkpoint(self, task: str) -> None:
        """Clear run checkpoint after successful completion."""
        checkpoint_path = self._get_run_checkpoint_path(task)
        try:
            if checkpoint_path.exists():
                checkpoint_path.unlink()
        except Exception as e:
            print(f"⚠️ Could not clear run checkpoint: {e}")
