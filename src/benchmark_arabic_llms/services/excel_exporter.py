"""
This file manages exporting benchmark results to Excel files.
It flattens nested reports, appends new results, and generates combined summaries for all benchmark tasks.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class ExcelExporter:
    """Handles exporting and appending benchmark results to Excel files."""

    def __init__(self, excel_dir: Path):
        self.excel_dir = excel_dir
        self.excel_dir.mkdir(parents=True, exist_ok=True)

    def export_result(self, report: Dict[str, Any], case: str) -> None:
        """
        Export benchmark result to Excel file, appending to existing data.
        Prevents duplicate exports by checking for existing entries.

        Args:
            report: The benchmark report dictionary
            case: The task case (summarization, qa, sarcasm)
        """
        excel_path = self.excel_dir / f"{case}_results.xlsx"

        flattened_result = self._flatten_report(report)

        if excel_path.exists():
            try:
                existing_df = pd.read_excel(excel_path)
                
                # Check for duplicate: same model, task, and very recent timestamp (within 5 seconds)
                # This prevents accidental double-clicks or rapid re-exports
                if not existing_df.empty and self._is_likely_duplicate(existing_df, flattened_result):
                    print(f"⚠️ Skipping export: Duplicate entry detected (same model & task within 5 seconds)")
                    return
                
                new_df = pd.concat(
                    [existing_df, pd.DataFrame([flattened_result])], ignore_index=True
                )
            except Exception as e:
                print(f"Warning: Could not read existing Excel file: {e}")
                new_df = pd.DataFrame([flattened_result])
        else:
            new_df = pd.DataFrame([flattened_result])

        try:
            new_df.to_excel(excel_path, index=False)
            print(f"✓ Results appended to Excel: {excel_path}")
        except Exception as e:
            print(f"✗ Failed to save Excel file: {e}")

    def export_current_run_only(self, report: Dict[str, Any], case: str) -> Path:
        """
        Export only the current run to a separate Excel file for download.

        Args:
            report: The benchmark report dictionary
            case: The task case (summarization, qa, sarcasm)

        Returns:
            Path to the exported Excel file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_run_path = self.excel_dir / f"{case}_current_run_{timestamp}.xlsx"

        flattened_result = self._flatten_report(report)
        df = pd.DataFrame([flattened_result])

        try:
            df.to_excel(current_run_path, index=False)
            print(f"✓ Current run exported: {current_run_path}")
            return current_run_path
        except Exception as e:
            print(f"✗ Failed to export current run: {e}")
            return None

    def export_detailed_samples(
        self, log_dir: Path, case: str, n_samples: int = None
    ) -> Path:
        """
        Export detailed sample data with inputs, outputs, expected results, and judge responses.
        Only exports the most recent run (last n_samples entries from the log).

        Args:
            log_dir: Directory containing the log files
            case: The task case (summarization, qa, sarcasm)
            n_samples: Number of samples in the current run (if None, exports all)

        Returns:
            Path to the exported Excel file with detailed samples
        """
        import json
        from collections import deque

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detailed_path = self.excel_dir / f"{case}_detailed_samples_{timestamp}.xlsx"

        # Read JSONL log file
        jsonl_path = log_dir / f"{case}_logs.jsonl"

        if not jsonl_path.exists():
            print(f"Warning: Log file not found: {jsonl_path}")
            return None

        try:
            # Parse JSONL file with bounded memory.
            all_count = 0
            if n_samples is not None and n_samples > 0:
                recent_samples = deque(maxlen=n_samples)
            else:
                recent_samples = []

            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        sample = json.loads(line)
                        all_count += 1
                        if isinstance(recent_samples, deque):
                            recent_samples.append(sample)
                        else:
                            recent_samples.append(sample)

            if all_count == 0:
                print(f"Warning: No samples found in {jsonl_path}")
                return None

            # Get only the current run samples (last n_samples entries)
            if n_samples is not None and n_samples > 0:
                samples = list(recent_samples)
                print(
                    f"✓ Exporting {len(samples)} samples from current run (out of {all_count} total)"
                )
            else:
                samples = recent_samples
                print(f"✓ Exporting all {len(samples)} samples")

            # Build detailed dataframe
            detailed_data = []
            for sample in samples:
                row = {
                    "Model": sample.get("model_name", "Unknown"),
                    "Example_Number": sample.get("example_number", ""),
                    "Task": sample.get("task", ""),
                    "Timestamp": sample.get("timestamp", ""),
                }

                # Add input data (varies by task)
                input_data = sample.get("input_data", {})
                if case == "summarization":
                    row["Input_Text"] = input_data.get("text", "")
                elif case == "question_answering":
                    row["Input_Text"] = input_data.get("text", input_data.get("context", ""))
                    row["Question"] = input_data.get("question", "")
                elif case == "sarcasm":
                    row["Input_Text"] = input_data.get("text", "")

                # Add expected output and model output
                row["Expected_Output"] = sample.get("expected_output", "")
                row["Model_Output"] = sample.get("llm_output", "")

                # Add match information
                row["Match"] = "Yes" if sample.get("match", False) else "No"
                row["Match_Type"] = sample.get("match_type", "exact")

                # Add LLM judge information (handle when semantic matching is disabled)
                if sample.get("match_type") == "semantic":
                    row["Match_Confidence"] = sample.get("match_confidence", 0.0)
                    row["Judge_Explanation"] = sample.get("match_explanation", "")
                else:
                    row["Match_Confidence"] = "N/A"
                    row["Judge_Explanation"] = "N/A (Exact matching used)"

                detailed_data.append(row)

            # Keep only the latest record per model/task/example when resumed runs append duplicates.
            if detailed_data:
                deduped = {}
                for row in detailed_data:
                    key = (row.get("Model"), row.get("Task"), row.get("Example_Number"))
                    deduped[key] = row
                detailed_data = list(deduped.values())

            # Create DataFrame and sort by Model and Example_Number
            df = pd.DataFrame(detailed_data)
            
            # Sort by Model (ascending) and then by Example_Number (ascending)
            if not df.empty and 'Model' in df.columns and 'Example_Number' in df.columns:
                df = df.sort_values(by=['Model', 'Example_Number'], ascending=[True, True])
                print(f"✓ Sorted {len(df)} samples by Model and Example_Number")
            
            df.to_excel(detailed_path, index=False)
            print(f"✓ Detailed samples exported: {detailed_path}")
            return detailed_path

        except Exception as e:
            print(f"✗ Failed to export detailed samples: {e}")
            return None

    def _is_likely_duplicate(self, existing_df: pd.DataFrame, new_result: Dict[str, Any]) -> bool:
        """
        Check if new result is likely a duplicate of a recent entry.
        Prevents accidental double-exports from button clicks or retries.
        
        Args:
            existing_df: Existing DataFrame with previous results
            new_result: New result to check
        
        Returns:
            True if likely duplicate, False otherwise
        """
        if existing_df.empty:
            return False
        
        try:
            # Get the most recent row
            last_row = existing_df.iloc[-1]
            
            # Check if same model and task
            same_model = str(last_row.get('model', '')) == str(new_result.get('model', ''))
            same_task = str(last_row.get('task', '')) == str(new_result.get('task', ''))
            same_examples = int(last_row.get('n_examples', -1)) == int(new_result.get('n_examples', -2))
            
            if same_model and same_task and same_examples:
                # Check if timestamps are within 5 seconds (likely duplicate)
                if 'timestamp' in last_row.index:
                    last_time = pd.to_datetime(last_row['timestamp'])
                    new_time = pd.to_datetime(new_result['timestamp'])
                    time_diff = abs((new_time - last_time).total_seconds())
                    
                    if time_diff < 5:  # Within 5 seconds = likely duplicate
                        return True
            
            return False
        except Exception as e:
            # If any error in checking, allow the export (fail-safe)
            print(f"Warning: Could not check for duplicate: {e}")
            return False

    def _flatten_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested report structure for Excel export.
        """
        flattened = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task": report.get("task", ""),
            "model": report.get("model", ""),
            "n_examples": report.get("n_examples", 0),
            "n_errors": report.get("n_errors", 0),
            "api_success_rate": report.get("api_success_rate", 0.0),
        }

        semantic_enabled = report.get("semantic_matching_enabled", False)

        if semantic_enabled:
            flattened.update(
                {
                    "semantic_matching_enabled": "Yes",
                    "semantic_matches": report.get("semantic_matches", 0),
                    "semantic_match_rate": round(
                        report.get("semantic_match_rate", 0.0), 4
                    ),
                    "avg_semantic_confidence": round(
                        report.get("avg_semantic_confidence", 0.0), 4
                    ),
                }
            )
        else:
            flattened.update(
                {
                    "semantic_matching_enabled": "No",
                    "semantic_matches": "N/A",
                    "semantic_match_rate": "N/A",
                    "avg_semantic_confidence": "N/A",
                }
            )

        scores = report.get("scores", {})
        if report.get("task") == "summarization":
            self._flatten_summarization_scores(scores, flattened)
        elif report.get("task") == "question_answering":
            self._flatten_qa_scores(scores, flattened)
        elif report.get("task") == "sarcasm":
            self._flatten_sarcasm_scores(scores, flattened)

        return flattened

    def _flatten_summarization_scores(
        self, scores: Dict[str, Any], flattened: Dict[str, Any]
    ) -> None:
        """Flatten summarization scores (ROUGE, BLEU, METEOR, BERTScore)."""
        flattened.update(
            {
                "rouge1": scores.get("ROUGE1", scores.get("rouge1", 0.0)),
                "rougeL": scores.get("ROUGEL", scores.get("rougeL", 0.0)),
                "bleu": scores.get("BLEU", scores.get("bleu", 0.0)),
                "meteor": scores.get("METEOR", scores.get("meteor", 0.0)),
                "bert_score": scores.get("BERTScore", scores.get("bert_score", 0.0)),
            }
        )

    def _flatten_qa_scores(
        self, scores: Dict[str, Any], flattened: Dict[str, Any]
    ) -> None:
        """Flatten QA scores."""
        flattened.update(
            {
                "accuracy": scores.get("Accuracy", scores.get("accuracy", scores.get("EM", scores.get("em", 0.0)))),
                "em": scores.get("EM", scores.get("em", scores.get("Accuracy", scores.get("accuracy", 0.0)))),
                "f1": scores.get("F1", scores.get("f1", 0.0)),
                "rouge1": scores.get("ROUGE1", scores.get("rouge1", 0.0)),
                "rougeL": scores.get("ROUGEL", scores.get("rougeL", scores.get("ROUGE", scores.get("rouge", 0.0)))),
                "bleu": scores.get("BLEU", scores.get("bleu", 0.0)),
                "meteor": scores.get("METEOR", scores.get("meteor", 0.0)),
                "bert_score": scores.get("BERTScore", scores.get("bert_score", 0.0)),
            }
        )

    def _flatten_sarcasm_scores(
        self, scores: Dict[str, Any], flattened: Dict[str, Any]
    ) -> None:
        """Flatten sarcasm detection scores."""
        flattened.update(
            {
                "accuracy": scores.get("Accuracy", scores.get("accuracy", 0.0)),
                "f1": scores.get("F1", scores.get("f1", 0.0)),
                "precision": scores.get("Precision", scores.get("precision", 0.0)),
                "recall": scores.get("Recall", scores.get("recall", 0.0)),
                "roc_auc": scores.get("ROC_AUC", scores.get("roc_auc", 0.0)),
            }
        )

    def get_results_summary(self, case: str) -> pd.DataFrame:
        """Get summary of all results for a specific case."""
        excel_path = self.excel_dir / f"{case}_results.xlsx"

        if not excel_path.exists():
            return pd.DataFrame()

        try:
            return pd.read_excel(excel_path)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return pd.DataFrame()

    def export_all_cases_summary(self) -> None:
        """Export a combined summary of all cases to a single Excel file."""
        summary_path = self.excel_dir / "all_results_summary.xlsx"

        all_data = []
        for case in ["summarization", "question_answering", "sarcasm"]:
            case_data = self.get_results_summary(case)
            if not case_data.empty:
                all_data.append(case_data)

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            try:
                combined_df.to_excel(summary_path, index=False)
                print(f"✓ Combined summary saved: {summary_path}")
            except Exception as e:
                print(f"✗ Failed to save combined summary: {e}")
        else:
            print("No data available for combined summary")

    def export_model_comparison(self, model_results: Dict[str, Any], case: str) -> Path:
        """
        Export comparison of multiple models side-by-side.

        Args:
            model_results: Dictionary with model names as keys and their results as values
            case: The task case (summarization, qa, sarcasm)

        Returns:
            Path to the exported Excel file with comparison
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_path = self.excel_dir / f"{case}_model_comparison_{timestamp}.xlsx"

        try:
            # Build comparison data
            comparison_data = []

            for model_name, model_data in model_results.items():
                scores = model_data.get("scores", {})
                stats = model_data.get("stats", {})

                row = {
                    "Model": model_name,
                    "Total_Examples": stats.get("n_examples", 0),
                    "API_Errors": stats.get("n_errors", 0),
                }

                # Add success rate
                n_examples = stats.get("n_examples", 1)
                n_errors = stats.get("n_errors", 0)
                success_rate = (
                    (n_examples - n_errors) / max(n_examples, 1)
                    if n_examples > 0
                    else 0
                )
                row["API_Success_Rate"] = success_rate

                # Add task-specific scores
                if case == "summarization":
                    row.update(
                        {
                            "ROUGE1": scores.get("ROUGE1", scores.get("rouge1", "N/A")),
                            "ROUGEL": scores.get("ROUGEL", scores.get("rougeL", "N/A")),
                            "BLEU": scores.get("BLEU", scores.get("bleu", "N/A")),
                            "METEOR": scores.get("METEOR", scores.get("meteor", "N/A")),
                            "BERTScore": scores.get("BERTScore", scores.get("bert_score", "N/A")),
                        }
                    )
                elif case == "question_answering":
                    row.update(
                        {
                            "Accuracy": scores.get("Accuracy", scores.get("accuracy", scores.get("EM", "N/A"))),
                            "EM": scores.get("EM", scores.get("em", scores.get("Accuracy", "N/A"))),
                            "F1": scores.get("F1", scores.get("f1", "N/A")),
                            "ROUGE1": scores.get("ROUGE1", scores.get("rouge1", "N/A")),
                            "ROUGEL": scores.get("ROUGEL", scores.get("rougeL", scores.get("ROUGE", "N/A"))),
                            "BLEU": scores.get("BLEU", scores.get("bleu", "N/A")),
                            "METEOR": scores.get("METEOR", scores.get("meteor", "N/A")),
                            "BERTScore": scores.get("BERTScore", scores.get("bert_score", "N/A")),
                        }
                    )
                elif case == "sarcasm":
                    row.update(
                        {
                            "Accuracy": scores.get("Accuracy", scores.get("accuracy", "N/A")),
                            "F1": scores.get("F1", scores.get("f1", "N/A")),
                            "Precision": scores.get("Precision", scores.get("precision", "N/A")),
                            "Recall": scores.get("Recall", scores.get("recall", "N/A")),
                            "ROC_AUC": scores.get("ROC_AUC", scores.get("roc_auc", "N/A")),
                        }
                    )


                # Add semantic matching stats if available
                if stats.get("semantic_matching_enabled", False):
                    row.update(
                        {
                            "Semantic_Matches": stats.get("semantic_matches", 0),
                            "Semantic_Match_Rate": stats.get(
                                "semantic_match_rate", 0.0
                            ),
                            "Avg_Semantic_Confidence": stats.get(
                                "avg_semantic_confidence", 0.0
                            ),
                        }
                    )

                comparison_data.append(row)

            # Create DataFrame and export
            if comparison_data:
                df = pd.DataFrame(comparison_data)
                df.to_excel(comparison_path, index=False)
                print(f"✓ Model comparison exported: {comparison_path}")
                return comparison_path
            else:
                print("No comparison data to export")
                return None

        except Exception as e:
            print(f"✗ Failed to export model comparison: {e}")
            return None
