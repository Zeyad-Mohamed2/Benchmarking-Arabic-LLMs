"""
This file defines the BenchmarkLogger, which manages structured and human-readable logging for benchmark runs.
It records example results, semantic match details, summaries, and errors using both JSONL and text logs for traceability and analysis.
"""

import json
import logging
from typing import Dict
from pathlib import Path
from datetime import datetime
from typing import Optional

class BenchmarkLogger:
    """Handles logging of benchmark results with proper application logging."""

    def __init__(
        self,
        log_dir: Path,
        task: str,
        semantic_matcher=None,
        clear_log: bool = False,
        resume_from_sample: Optional[int] = None,
        model_name: Optional[str] = None,
        fast_resume_mode: bool = False,
    ):
        """
        Initialize logger.

        Args:
            log_dir: Directory to save logs
            task: Task name (e.g., 'qa', 'summarization')
            semantic_matcher: Optional SemanticMatcher for intelligent comparison
            clear_log: Whether to clear existing JSONL log (use True for first model in a run)
            resume_from_sample: If resuming from checkpoint, the last completed sample number (1-based)
            model_name: Model name for filtering log entries during truncation
            fast_resume_mode: If True, skip costly JSONL truncation and rely on export-time deduplication
        """
        self.log_dir = log_dir
        self.task = task
        self.semantic_matcher = semantic_matcher
        self.model_name = model_name
        self.fast_resume_mode = fast_resume_mode
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Clear JSONL log file only if requested (for fresh run)
        if clear_log:
            self._clear_jsonl_log()
        # If resuming from checkpoint, truncate log to checkpoint position for this model only
        elif resume_from_sample is not None and model_name is not None:
            if self.fast_resume_mode:
                logging.getLogger(f"BenchmarkLogger.{task}").info(
                    "Fast resume mode enabled: skipping log truncation"
                )
            else:
                self._truncate_log_to_position(resume_from_sample, model_name)

        # Setup application logging (for events, errors, progress)
        self._setup_app_logging()

        # Log initialization
        self.logger.info(f"BenchmarkLogger initialized for task '{task}' in {log_dir}")
        if resume_from_sample is not None:
            self.logger.info(f"Resuming from sample {resume_from_sample} - log truncated to remove incomplete entries")

        # Open persistent file handles (must come after any truncation/clearing)
        self._jsonl_handle = open(self.log_dir / f"{self.task}_logs.jsonl", "a", encoding="utf-8")
        self._text_handle = open(self.log_dir / f"{self.task}_outputs.log", "a", encoding="utf-8")

    def _setup_app_logging(self) -> None:
        """Configure application logging for events, errors, and progress."""
        self.logger = logging.getLogger(f"BenchmarkLogger.{self.task}")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Application log file (for events, errors, progress)
        app_log_file = self.log_dir / f"{self.task}_application.log"
        file_handler = logging.FileHandler(app_log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter with timestamp and level
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _clear_jsonl_log(self) -> None:
        """Clear JSONL log file at start of new run to prevent duplicates."""
        json_log_file = self.log_dir / f"{self.task}_logs.jsonl"
        try:
            if json_log_file.exists():
                json_log_file.unlink()
                # Create empty file
                json_log_file.touch()
        except Exception as e:
            print(f"⚠️ Could not clear log file: {e}")

    def _truncate_log_to_position(self, last_completed_sample: int, model_name: str) -> None:
        """Truncate JSONL log to only include entries up to the checkpoint position for a specific model.
        
        This prevents duplicate entries when resuming from a checkpoint. Only affects the specified model's entries,
        leaving other models' entries intact.
        
        Args:
            last_completed_sample: The last successfully completed sample number (1-based)
            model_name: Name of the model whose entries should be truncated
        """
        json_log_file = self.log_dir / f"{self.task}_logs.jsonl"
        
        if not json_log_file.exists():
            return  # Nothing to truncate
        
        try:
            # Read all existing entries
            entries_to_keep = []
            truncated_count = 0
            with open(json_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_model = entry.get('model_name', '')
                        example_num = entry.get('example_number', 0)
                        
                        # Keep entry if it's from a different model OR within checkpoint position
                        if entry_model != model_name or example_num <= last_completed_sample:
                            entries_to_keep.append(line)
                        else:
                            truncated_count += 1
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
            
            # Rewrite the file with only the entries to keep
            with open(json_log_file, 'w', encoding='utf-8') as f:
                f.writelines(entries_to_keep)
            
            print(f"📝 Truncated {truncated_count} entries for {model_name} (keeping samples 1-{last_completed_sample})")
            
        except Exception as e:
            print(f"⚠️ Could not truncate log file: {e}")

    def log_example(
        self,
        example_num: int,
        item: Dict,
        prompt: str,
        output: str,
        reference: str,
        normalized_output: Optional[str] = None,
        normalized_reference: Optional[str] = None,
        model_name: str = "Unknown",
        semantic_match: Optional[bool] = None,
        semantic_explanation: Optional[str] = None,
        semantic_confidence: Optional[float] = None,
    ) -> None:
        """Log a single example result with optional normalized values."""
        self.logger.debug(f"Processing example {example_num}")

        try:
            log_entry = self._create_log_entry(
                example_num,
                item,
                prompt,
                output,
                reference,
                model_name,
                normalized_output=normalized_output,
                normalized_reference=normalized_reference,
                semantic_match=semantic_match,
                semantic_explanation=semantic_explanation,
                semantic_confidence=semantic_confidence,
            )

            # Save structured data (not logging, just data persistence)
            self._write_json_log(log_entry)
            self._write_text_log(log_entry)

            # Log the outcome
            match_status = "MATCH" if log_entry["match"] else "NO MATCH"
            if log_entry.get("match_type") == "semantic":
                confidence = log_entry.get("match_confidence", 0.0)
                self.logger.info(
                    f"Example {example_num}: {match_status} "
                    f"(semantic, confidence: {confidence:.2f})"
                )
            else:
                self.logger.info(f"Example {example_num}: {match_status} (exact)")

        except Exception as e:
            self.logger.error(
                f"Failed to process example {example_num}: {str(e)}", exc_info=True
            )
            raise

    def log_error_example(
        self,
        example_num: int,
        item: Dict,
        error_msg: str,
        error_type: str = "unknown",
        error_details: Optional[Dict] = None,
        model_name: str = "Unknown",
    ) -> None:
        """Log a failed example with detailed error information.
        
        Args:
            example_num: Example number (1-based)
            item: Input data
            error_msg: Error message
            error_type: Type of error (e.g., 'rate_limit', 'payment', 'timeout', 'api_error')
            error_details: Additional error details (status code, headers, etc.)
            model_name: Model name
        """
        self.logger.error(f"Example {example_num} failed: {error_type} - {error_msg}")

        try:
            log_entry = {
                "model_name": model_name,
                "task": self.task,
                "example_number": example_num,
                "input_data": item,
                "status": "error",
                "error_type": error_type,
                "error_message": error_msg,
                "error_details": error_details or {},
                "timestamp": datetime.now().isoformat(),
            }

            # Save to JSONL
            self._write_json_log(log_entry)
            
            # Write human-readable error log
            self._write_error_text_log(log_entry)

        except Exception as e:
            self.logger.error(
                f"Failed to log error for example {example_num}: {str(e)}", exc_info=True
            )

    def _create_log_entry(
        self,
        example_num: int,
        item: Dict,
        prompt: str,
        output: str,
        reference: str,
        model_name: str,
        normalized_output=None,
        normalized_reference=None,
        semantic_match: Optional[bool] = None,
        semantic_explanation: Optional[str] = None,
        semantic_confidence: Optional[float] = None,
    ) -> Dict:
        """Create a log entry for an example with normalized comparison.

        Semantic match values are passed in from BenchmarkRunner (already computed
        there) to avoid a second LLM-judge API call per example.
        """
        # Use normalized values for comparison if provided, otherwise use originals
        comparison_output = normalized_output if normalized_output is not None else output
        comparison_reference = normalized_reference if normalized_reference is not None else reference

        # Determine match using normalized values
        is_exact_match = comparison_output.strip() == comparison_reference.strip()

        # Create log entry with ORIGINAL values for transparency
        log_entry = {
            "model_name": model_name,
            "task": self.task,
            "example_number": example_num,
            "input_data": item,
            "expected_output": reference,
            "llm_output": output,
            "match": is_exact_match,
            "match_type": "exact",
            "timestamp": datetime.now().isoformat(),
        }

        # Use pre-computed semantic result passed from BenchmarkRunner.
        # This avoids calling the LLM judge a second time for the same example.
        if self.semantic_matcher and semantic_match is not None:
            log_entry.update(
                {
                    "match": semantic_match,
                    "match_type": "semantic",
                    "match_confidence": semantic_confidence if semantic_confidence is not None else 0.5,
                    "match_explanation": semantic_explanation or "",
                }
            )

        return log_entry

    def _write_json_log(self, log_entry: Dict) -> None:
        """Write structured data to JSON lines file (data persistence, not logging)."""
        try:
            self._jsonl_handle.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            self._jsonl_handle.flush()
            self.logger.debug(f"Wrote JSON entry for example {log_entry['example_number']}")
        except IOError as e:
            self.logger.error(f"Failed to write JSON log: {str(e)}")
            raise

    def _write_text_log(self, log_entry: Dict) -> None:
        """Write human-readable output to text file (reporting, not logging)."""
        try:
            display_text = self._format_display_text(log_entry)
            self._text_handle.write(display_text + "\n" + "=" * 80 + "\n")
            self._text_handle.flush()
            self.logger.debug(f"Wrote text entry for example {log_entry['example_number']}")
        except IOError as e:
            self.logger.error(f"Failed to write text log: {str(e)}")
            raise

    def _format_display_text(self, log_entry: Dict) -> str:
        """Format log entry for display."""
        match_icon = "✅" if log_entry["match"] else "❌"
        match_status = "YES" if log_entry["match"] else "NO"

        output = f"\n{'='*60}\n"
        output += f"EXAMPLE {log_entry['example_number']}\n"
        output += f"{'='*60}\n"
        output += f"Timestamp: {datetime.now().isoformat()}\n"
        output += f"🎯 EXPECTED OUTPUT: {log_entry['expected_output']}\n"
        output += f"🤖 LLM OUTPUT: {log_entry['llm_output']}\n"
        output += f"{match_icon} MATCH: {match_status}\n"

        if log_entry.get("match_type") == "semantic":
            confidence = log_entry.get("match_confidence", 0.0)
            explanation = log_entry.get("match_explanation", "")
            output += f"🧠 SEMANTIC MATCH (Confidence: {confidence:.2f})\n"
            output += f"💬 EXPLANATION: {explanation}\n"

        return output

    def _write_error_text_log(self, log_entry: Dict) -> None:
        """Write human-readable error output to text file."""
        try:
            display_text = self._format_error_display_text(log_entry)
            self._text_handle.write(display_text + "\n" + "=" * 80 + "\n")
            self._text_handle.flush()
            self.logger.debug(f"Wrote error text entry for example {log_entry['example_number']}")
        except IOError as e:
            self.logger.error(f"Failed to write error text log: {str(e)}")
            raise

    def _format_error_display_text(self, log_entry: Dict) -> str:
        """Format error log entry for display."""
        output = f"\n{'='*60}\n"
        output += f"EXAMPLE {log_entry['example_number']} - ERROR\n"
        output += f"{'='*60}\n"
        output += f"Timestamp: {log_entry['timestamp']}\n"
        output += f"❌ ERROR TYPE: {log_entry['error_type']}\n"
        output += f"📛 ERROR MESSAGE: {log_entry['error_message']}\n"
        
        if log_entry.get('error_details'):
            output += f"🔍 ERROR DETAILS:\n"
            for key, value in log_entry['error_details'].items():
                output += f"   - {key}: {value}\n"
        
        return output

    def log_summary(self, total: int, matches: int, duration: float) -> None:
        """Log benchmark summary statistics."""
        accuracy = (matches / total * 100) if total > 0 else 0
        self.logger.info("=" * 60)
        self.logger.info("BENCHMARK SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Task: {self.task}")
        self.logger.info(f"Total examples: {total}")
        self.logger.info(f"Matches: {matches}")
        self.logger.info(f"Accuracy: {accuracy:.2f}%")
        self.logger.info(f"Duration: {duration:.2f}s")
        self.logger.info("=" * 60)

    def log_error(self, message: str, exception: Exception = None) -> None:
        """Log an error with optional exception details."""
        if exception:
            self.logger.error(message, exc_info=True)
        else:
            self.logger.error(message)

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def __del__(self):
        """Cleanup handlers on deletion."""
        if hasattr(self, "logger"):
            self.logger.info(f"Shutting down BenchmarkLogger for task '{self.task}'")
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
        # Close persistent file handles
        for attr in ("_jsonl_handle", "_text_handle"):
            handle = getattr(self, attr, None)
            if handle and not handle.closed:
                handle.close()
