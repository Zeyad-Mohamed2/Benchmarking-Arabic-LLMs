"""
This file defines the BenchmarkRunner, which orchestrates the entire benchmark workflow.
It processes dataset examples, generates model predictions, evaluates them, logs results, and computes performance and semantic matching statistics.
"""

import re
from tqdm import tqdm
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

from benchmark_arabic_llms.core.enums import BenchmarkTask
from benchmark_arabic_llms.services.llm_client import LLMClient
from benchmark_arabic_llms.evaluation.evaluator import Evaluator
from benchmark_arabic_llms.core.exceptions import (
    EvaluationError,
    ClientError,
    RateLimitError,
    PaymentError,
    TokenLimitError,
    TimeoutError,
)
from benchmark_arabic_llms.evaluation.logger import BenchmarkLogger
from benchmark_arabic_llms.evaluation.prompt_builder import PromptBuilder
from benchmark_arabic_llms.evaluation.llm_judge import SemanticMatcher
from benchmark_arabic_llms.config.data_paths import (
    QA_REPORT_PATH,
    SARCASM_REPORT_PATH,
    SUMMARIZATION_REPORT_PATH,
)


class BenchmarkRunner:
    """Orchestrates the benchmark execution."""

    # Pre-compiled once at class level – avoids recompiling on every example
    _THINK_RE = re.compile(r'<think>.*?</think>', re.IGNORECASE | re.DOTALL)

    def __init__(
        self,
        client: LLMClient,
        task: BenchmarkTask,
        prompt_template: str,
        log_dir: Path,
        semantic_matcher: Optional[SemanticMatcher] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        clear_log: bool = False,
        enable_checkpoint_mode: bool = False,
        checkpoint_interval: int = 50,
        checkpoint_data: Optional[Dict] = None,
        model_name: str = "Unknown",
        checkpoint_callback: Optional[Callable[[Dict], None]] = None,
        fast_resume_mode: bool = False,
    ):
        self.client = client
        self.task = task
        self.prompt_builder = PromptBuilder(prompt_template, task)
        self.evaluator = Evaluator(task)
        
        # Determine if we're resuming from checkpoint
        resume_from_sample = None
        if checkpoint_data is not None:
            resume_from_sample = checkpoint_data.get("last_sample_index", -1) + 1  # Convert 0-based index to 1-based sample number
            if resume_from_sample <= 0:
                resume_from_sample = None
        
        self.logger = BenchmarkLogger(
            log_dir,
            task.value,
            semantic_matcher,
            clear_log=clear_log,
            resume_from_sample=resume_from_sample,
            model_name=model_name,
            fast_resume_mode=fast_resume_mode,
        )
        self.semantic_matcher = semantic_matcher
        self.progress_callback = progress_callback
        self.log_dir = log_dir
        self.model_name = model_name

        # Checkpoint support
        self.enable_checkpoint_mode = enable_checkpoint_mode
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_counter = 0
        self.checkpoint_data = checkpoint_data
        self.checkpoint_callback = checkpoint_callback

        # Initialize or restore state
        if checkpoint_data:
            self._restore_from_checkpoint(checkpoint_data)
        else:
            self.predictions = []
            self.references = []
            self.errors = 0
            self.failed_samples = []
            self.semantic_matches = []
            self.semantic_confidences = []

        print(f"🔧 BenchmarkRunner initialized")
        print(f"   - semantic_matcher: {self.semantic_matcher is not None}")
        print(f"   - task: {self.task.value}")
        print(f"   - progress_callback: {self.progress_callback is not None}")
        print(f"   - checkpoint_mode: {self.enable_checkpoint_mode}")
        if self.enable_checkpoint_mode:
            print(f"   - checkpoint_interval: {self.checkpoint_interval}")

    def _restore_from_checkpoint(self, checkpoint_data: Dict) -> None:
        """Restore state from checkpoint."""
        self.predictions = checkpoint_data.get("predictions", [])
        self.references = checkpoint_data.get("references", [])
        self.errors = checkpoint_data.get("errors", 0)
        self.failed_samples = checkpoint_data.get("failed_samples", [])
        self.semantic_matches = checkpoint_data.get("semantic_matches", [])
        self.semantic_confidences = checkpoint_data.get("semantic_confidences", [])
        
        print(f"📍 Restored state: {len(self.predictions)} samples completed")

    def process_examples(self, data: List[Dict]) -> None:
        """Process all examples and generate predictions with retry logic."""
        total_examples = len(data)
        
        # Determine start index (for resume)
        start_index = len(self.predictions) if self.checkpoint_data else 0
        
        if start_index > 0:
            print(f"🔄 Resuming from sample {start_index + 1}/{total_examples}")
        else:
            print(f"\n📊 Processing {total_examples} examples...")

        # Report initialization
        if self.progress_callback:
            self.progress_callback(start_index, total_examples, "Initializing processing...")

        # Initial pass (start from checkpoint position)
        for i in tqdm(range(start_index, total_examples), desc="Processing examples", initial=start_index, total=total_examples):
            item = data[i]
            try:
                # Update progress before processing
                if self.progress_callback:
                    self.progress_callback(
                        i,
                        total_examples,
                        f"Processing example {i + 1}/{total_examples}",
                    )

                self._process_single_example(i + 1, item)
                
                # Checkpoint logic (ONLY if enabled)
                if self.enable_checkpoint_mode:
                    self.checkpoint_counter += 1
                    if self.checkpoint_counter >= self.checkpoint_interval:
                        self._save_checkpoint_to_orchestrator(i, total_examples)
                        self.checkpoint_counter = 0

            except Exception as e:
                print(f"❌ Error processing example {i+1}: {e}")
                self._handle_error(
                    i + 1, item, e
                )  # Pass the exception object instead of string

        # Retry pass for failed samples
        if self.failed_samples:
            print(f"\n🔄 Retrying {len(self.failed_samples)} failed samples...")
            self._retry_failed_samples(total_examples)

        # Export unrecoverable failures if any remain
        if self.failed_samples:
            self._export_unrecoverable_failures()

        # Report completion
        if self.progress_callback:
            self.progress_callback(
                total_examples, total_examples, "Processing completed"
            )

        # Print summary
        successful = total_examples - len(self.failed_samples)
        print(f"\n✅ Completed: {successful}/{total_examples} samples")
        if self.failed_samples:
            print(
                f"❌ Failed: {len(self.failed_samples)} samples (exported to failures.json)"
            )

    def _remove_thinking_tags(self, text: str) -> str:
        """
        Remove <think></think> tags and their content from model output.
        Some reasoning models output their thought process in these tags.
        
        Args:
            text: Raw model output that may contain thinking tags
            
        Returns:
            Cleaned text with thinking tags removed
        """
        if not text:
            return text
        
        # Use the pre-compiled class-level pattern (avoids recompilation per example)
        return self._THINK_RE.sub('', text).strip()
    
    def _normalize_sarcasm_labels(self, output: str, reference: str) -> tuple[str, str]:
        """
        Normalize sarcasm detection labels to a common format.
        Handles conversion between Arabic text, English text, and binary formats.

        Args:
            output: Model output (can be Arabic, English, or binary)
            reference: Reference label (can be Arabic, English, or binary)

        Returns:
            Tuple of (normalized_output, normalized_reference) both in Arabic format
        """
        # Comprehensive mapping to Arabic format
        label_mapping = {
            # Arabic
            "ساخر": "ساخر",
            "غير ساخر": "غير ساخر",
            "سخرية": "ساخر",
            "غير سخرية": "غير ساخر",
            # English
            "sarcastic": "ساخر",
            "not sarcastic": "غير ساخر",
            "yes": "ساخر",
            "no": "غير ساخر",
            # Binary
            "1": "ساخر",
            "0": "غير ساخر",
            # Additional variations
            "true": "ساخر",
            "false": "غير ساخر",
        }

        def normalize_single_label(label: str) -> str:
            """Normalize a single label."""
            if label is None:
                return "غير ساخر"

            # Convert to string and clean
            label_str = str(label).strip().lower()

            # Direct mapping
            if label_str in label_mapping:
                return label_mapping[label_str]

            # Try to extract from longer text (handle cases like model outputting extra text)
            if "ساخر" in label_str:
                if "غير" in label_str or "لا" in label_str or "ليس" in label_str:
                    return "غير ساخر"
                else:
                    return "ساخر"

            # Check for English keywords
            if "sarcas" in label_str:
                if "not" in label_str or "no" in label_str:
                    return "غير ساخر"
                else:
                    return "ساخر"

            # Check for binary in text
            if label_str == "1" or label_str == "true":
                return "ساخر"
            if label_str == "0" or label_str == "false":
                return "غير ساخر"

            # Default to non-sarcastic if unclear
            print(
                f"⚠️ Warning: Could not normalize label '{label}', defaulting to 'غير ساخر'"
            )
            return "غير ساخر"

        normalized_output = normalize_single_label(output)
        normalized_reference = normalize_single_label(reference)

        return normalized_output, normalized_reference

    def _process_single_example(
        self, example_num: int, item: Dict, is_retry: bool = False
    ) -> None:
        """Process a single example."""
        prompt, reference = self.prompt_builder.build(item)

        if not prompt.strip():
            print(f"⚠️ Warning: Empty prompt for example {example_num}")
            raise ValueError("Empty prompt generated")

        # Generate output
        output = self.client.generate(prompt).strip()
        
        # Remove thinking tags if present (e.g., <think>...</think>)
        output = self._remove_thinking_tags(output)

        output_str = str(output) if output is not None else ""
        reference_str = str(reference) if reference is not None else ""

        # Normalize for sarcasm task
        if self.task == BenchmarkTask.SARCASM:
            normalized_output, normalized_reference = self._normalize_sarcasm_labels(
                output_str, reference_str
            )
        else:
            normalized_output = output_str
            normalized_reference = reference_str

        # Update or append based on whether this is a retry
        if is_retry:
            # Update existing placeholder
            idx = example_num - 1
            self.predictions[idx] = normalized_output
            self.references[idx] = normalized_reference
        else:
            # First attempt - append
            self.predictions.append(normalized_output)
            self.references.append(normalized_reference)

        # Semantic tracking vars — filled in below if matcher is enabled
        _sem_match: Optional[bool] = None
        _sem_expl: Optional[str] = None
        _sem_conf: Optional[float] = None

        if self.semantic_matcher:
            if normalized_output and normalized_reference:
                try:
                    is_match, explanation, confidence = (
                        self.semantic_matcher.check_semantic_match(
                            normalized_output,
                            normalized_reference,
                            task_context=self.task.value,
                            input_data=item,
                        )
                    )
                    _sem_match, _sem_expl, _sem_conf = is_match, explanation, confidence

                    # Update or append based on retry status
                    if is_retry:
                        idx = example_num - 1
                        self.semantic_matches[idx] = is_match
                        self.semantic_confidences[idx] = confidence
                    else:
                        self.semantic_matches.append(is_match)
                        self.semantic_confidences.append(confidence)

                    match_symbol = "✅" if is_match else "❌"
                    print(
                        f"  {match_symbol} Example {example_num}: match={is_match}, confidence={confidence:.2f}"
                    )

                except Exception as e:
                    print(f"⚠️ Semantic matching failed for example {example_num}: {e}")
                    exact_match = (
                        normalized_output.strip() == normalized_reference.strip()
                    )
                    _sem_match = exact_match
                    _sem_expl = f"Fallback to exact match due to error: {e}"
                    _sem_conf = 1.0 if exact_match else 0.0

                    if is_retry:
                        idx = example_num - 1
                        self.semantic_matches[idx] = exact_match
                        self.semantic_confidences[idx] = _sem_conf
                    else:
                        self.semantic_matches.append(exact_match)
                        self.semantic_confidences.append(_sem_conf)
            else:
                print(
                    f"⚠️ Example {example_num}: Empty output or reference, marking as no match"
                )
                _sem_match, _sem_expl, _sem_conf = False, "Empty output or reference", 0.0

                if is_retry:
                    idx = example_num - 1
                    self.semantic_matches[idx] = False
                    self.semantic_confidences[idx] = 0.0
                else:
                    self.semantic_matches.append(False)
                    self.semantic_confidences.append(0.0)

        # Pass pre-computed semantic result so the logger doesn't call the judge again
        self.logger.log_example(
            example_num,
            item,
            prompt,
            output_str,  # Original output
            reference_str,  # Original reference
            normalized_output=normalized_output,
            normalized_reference=normalized_reference,
            model_name=getattr(self.client, "model", "Unknown"),
            semantic_match=_sem_match,
            semantic_explanation=_sem_expl,
            semantic_confidence=_sem_conf,
        )

    def _handle_error(self, index: int, item: Dict, error: Exception) -> None:
        """Handle processing error by tracking for retry and logging detailed error info.
        
        Args:
            index: Example number (1-based)
            item: Input data
            error: The exception that occurred
        """
        # Extract error type and details from exception
        error_type = "unknown"
        error_details = {}
        error_msg = str(error)
        
        # Determine error type and extract details
        if isinstance(error, RateLimitError):
            error_type = "rate_limit"
            error_details = error.error_details
            if error.retry_after:
                error_details["retry_after_seconds"] = error.retry_after
        elif isinstance(error, PaymentError):
            error_type = "payment"
            error_details = error.error_details
        elif isinstance(error, TokenLimitError):
            error_type = "token_limit"
            error_details = error.error_details
        elif isinstance(error, TimeoutError):
            error_type = "timeout"
            error_details = error.error_details
        elif isinstance(error, ClientError):
            error_type = error.error_type
            error_details = error.error_details
        elif isinstance(error, ValueError):
            error_type = "validation_error"
            error_details = {"error_class": type(error).__name__}
        else:
            error_type = "unknown"
            error_details = {"error_class": type(error).__name__}
        
        # Log the error with detailed information
        self.logger.log_error_example(
            example_num=index,
            item=item,
            error_msg=error_msg,
            error_type=error_type,
            error_details=error_details,
            model_name=getattr(self.client, "model", "Unknown"),
        )
        
        # Track for retry
        self.predictions.append("")
        self.references.append("")
        self.errors += 1

        # Track failed sample for retry
        self.failed_samples.append((index, item, error_msg))

        # Add placeholder for semantic stats if enabled
        if self.semantic_matcher:
            self.semantic_matches.append(False)
            self.semantic_confidences.append(0.0)

    def _retry_failed_samples(self, total_examples: int) -> None:
        """Retry all failed samples once with longer delays."""
        import time

        # Wait before retry
        print("⏸️  Waiting 10 seconds before retry...")
        time.sleep(10)

        retry_list = self.failed_samples.copy()
        self.failed_samples = []  # Clear for this retry pass

        for retry_index, (idx, item, prev_error) in enumerate(
            tqdm(retry_list, desc="Retrying failed samples"), start=1
        ):
            try:
                if self.progress_callback:
                    current = (
                        total_examples
                        - len(retry_list)
                        + retry_index
                    )
                    self.progress_callback(
                        current,
                        total_examples,
                        f"Retrying example {idx}",
                    )

                # Process the sample again with retry flag
                self._process_single_example(idx, item, is_retry=True)

                # Success - the prediction/reference was updated in place
                # Decrement error count since this sample is now successful
                self.errors -= 1
                print(f"✅ Retry successful for example {idx}")
                
            except Exception as e:
                print(f"❌ Retry failed for example {idx}: {e}")
                # Add back to failed list and log the error
                self.failed_samples.append((idx, item, str(e)))
                
                # Log the retry failure with detailed error info
                error_type = "unknown"
                error_details = {}
                
                if isinstance(e, RateLimitError):
                    error_type = "rate_limit"
                    error_details = e.error_details
                elif isinstance(e, PaymentError):
                    error_type = "payment"
                    error_details = e.error_details
                elif isinstance(e, TokenLimitError):
                    error_type = "token_limit"
                    error_details = e.error_details
                elif isinstance(e, TimeoutError):
                    error_type = "timeout"
                    error_details = e.error_details
                elif isinstance(e, ClientError):
                    error_type = e.error_type
                    error_details = e.error_details
                else:
                    error_type = "unknown"
                    error_details = {"error_class": type(e).__name__}
                
                error_details["retry_attempt"] = True
                
                self.logger.log_error_example(
                    example_num=idx,
                    item=item,
                    error_msg=str(e),
                    error_type=error_type,
                    error_details=error_details,
                    model_name=getattr(self.client, "model", "Unknown"),
                )

    def _export_unrecoverable_failures(self) -> None:
        """Export failed samples to JSON for manual review."""
        import json
        from datetime import datetime

        output_path = self.log_dir / f"{self.task.value}_unrecoverable_failures.json"

        failures_data = {
            "task": self.task.value,
            "timestamp": datetime.now().isoformat(),
            "total_failures": len(self.failed_samples),
            "failures": [
                {
                    "example_number": idx,
                    "input_data": item,
                    "error": error_msg,
                }
                for idx, item, error_msg in self.failed_samples
            ],
        }

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(failures_data, f, ensure_ascii=False, indent=2)
            print(f"📄 Exported failures to: {output_path}")
        except Exception as e:
            print(f"⚠️  Could not export failures: {e}")

    def evaluate(self) -> Dict[str, Any]:
        """Evaluate all predictions."""
        if self.errors == len(self.predictions):
            raise EvaluationError("All examples failed")

        return self.evaluator.evaluate(self.references, self.predictions)

    def get_report_path(self) -> Path:
        """Get the appropriate report path for the task."""
        report_paths = {
            BenchmarkTask.SUMMARIZATION: SUMMARIZATION_REPORT_PATH,
            BenchmarkTask.QA: QA_REPORT_PATH,
            BenchmarkTask.SARCASM: SARCASM_REPORT_PATH,
        }
        return report_paths.get(self.task, Path("default_report.json"))

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics including semantic matching stats."""
        total = len(self.predictions)
        
        # Count actual successful samples (non-empty predictions)
        successful_samples = sum(1 for p in self.predictions if p and p.strip())
        
        stats = {
            "n_examples": total,
            "n_errors": self.errors,
            "n_successful": successful_samples,
            "api_success_rate": (total - self.errors) / total if total > 0 else 0,
        }

        print(f"\n🔍 Getting stats:")
        print(f"   - Total examples: {total}")
        print(f"   - Successful: {successful_samples}")
        print(f"   - Errors: {self.errors}")
        print(f"   - semantic_matcher exists: {self.semantic_matcher is not None}")
        print(f"   - semantic_matches length: {len(self.semantic_matches)}")
        print(f"   - semantic_confidences length: {len(self.semantic_confidences)}")

        if self.semantic_matcher and len(self.semantic_matches) > 0:
            semantic_match_count = sum(self.semantic_matches)
            avg_confidence = (
                sum(self.semantic_confidences) / len(self.semantic_confidences)
                if self.semantic_confidences
                else 0.0
            )

            stats.update(
                {
                    "semantic_matching_enabled": True,
                    "semantic_matches": semantic_match_count,
                    "semantic_match_rate": (
                        semantic_match_count / successful_samples if successful_samples > 0 else 0
                    ),
                    "avg_semantic_confidence": avg_confidence,
                }
            )

            print(f"   ✅ Semantic stats added:")
            print(f"      - semantic_matches: {semantic_match_count}")
            print(
                f"      - semantic_match_rate: {semantic_match_count / successful_samples if successful_samples > 0 else 0:.2%}"
            )
            print(f"      - avg_confidence: {avg_confidence:.2f}")
        else:
            stats.update(
                {
                    "semantic_matching_enabled": False,
                }
            )
            print(f"   ❌ Semantic matching disabled or no data")

        return stats

    def _save_checkpoint_to_orchestrator(self, current_index: int, total: int) -> None:
        """Save checkpoint state via callback to orchestrator."""
        if not self.checkpoint_callback:
            return
        
        # Use .copy() so the callback receives a consistent snapshot and the
        # runner's live lists are not aliased into the checkpoint dict.
        checkpoint_state = {
            "last_sample_index": current_index,
            "total_samples": total,
            "predictions": self.predictions.copy(),
            "references": self.references.copy(),
            "errors": self.errors,
            "failed_samples": self.failed_samples.copy(),
            "semantic_matches": self.semantic_matches.copy(),
            "semantic_confidences": self.semantic_confidences.copy(),
        }
        
        try:
            self.checkpoint_callback(checkpoint_state)
            print(f"💾 Checkpoint saved at sample {current_index + 1}/{total}")
        except Exception as e:
            print(f"⚠️ Failed to save checkpoint: {e}")
