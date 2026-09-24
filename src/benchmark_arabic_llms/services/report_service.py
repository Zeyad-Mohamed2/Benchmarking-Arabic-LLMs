"""
This file defines the ReportService, which generates, saves, and exports benchmark reports.
It builds detailed task reports, saves them as JSON files, and appends results to Excel summaries for analysis.
"""

import json
from pathlib import Path
from typing import Dict, Any
from benchmark_arabic_llms.services.excel_exporter import ExcelExporter
from benchmark_arabic_llms.config.benchmark_config import BenchmarkConfig


class ReportService:
    """Handles all reporting operations."""

    def __init__(self, excel_dir: Path):
        self.excel_exporter = ExcelExporter(excel_dir)

    def generate_and_save_report(
        self,
        config: BenchmarkConfig,
        scores: Dict[str, Any],
        stats: Dict[str, Any],
        model: str,
        output_path: Path,
    ) -> Dict[str, Any]:
        """Generate report and save to all formats."""
        report = self._build_report(config, scores, stats, model)

        self._save_json_report(report, output_path)
        case_str = config.case if isinstance(config.case, str) else config.case.value
        self.excel_exporter.export_result(report, case_str)

        return report

    def export_current_run(self, report: Dict[str, Any], case: str) -> Path:
        """
        Export only the current run to a separate Excel file.

        Args:
            report: The benchmark report dictionary
            case: The task case (summarization, qa, sarcasm)

        Returns:
            Path to the exported Excel file
        """
        return self.excel_exporter.export_current_run_only(report, case)

    def export_detailed_samples(
        self, log_dir: Path, case: str, n_samples: int = None
    ) -> Path:
        """
        Export detailed sample data with inputs, outputs, expected results, and judge responses.
        Only exports the current run samples.

        Args:
            log_dir: Directory containing the log files
            case: The task case (summarization, qa, sarcasm)
            n_samples: Number of samples in the current run

        Returns:
            Path to the exported Excel file with detailed samples
        """
        return self.excel_exporter.export_detailed_samples(log_dir, case, n_samples)

    def export_model_comparison(self, model_results: Dict[str, Any], case: str) -> Path:
        """
        Export comparison of multiple models side-by-side.

        Args:
            model_results: Dictionary with model names as keys and their results as values
            case: The task case (summarization, qa, sarcasm)

        Returns:
            Path to the exported Excel file with comparison
        """
        return self.excel_exporter.export_model_comparison(model_results, case)

    def _build_report(
        self,
        config: BenchmarkConfig,
        scores: Dict[str, Any],
        stats: Dict[str, Any],
        model: str,
    ) -> Dict[str, Any]:
        """Build report dictionary with semantic matching stats."""
        task_name = config.case if isinstance(config.case, str) else config.case.value

        report = {
            "task": task_name,
            "dataset": str(config.dataset_path),
            "prompt_template": str(config.prompt_template_path),
            "model": model,
            "scores": scores,
            "n_examples": stats["n_examples"],
            "n_errors": stats["n_errors"],
            "api_success_rate": stats["api_success_rate"],
        }

        if stats.get("semantic_matching_enabled", False):
            report.update(
                {
                    "semantic_matching_enabled": True,
                    "semantic_matches": stats.get("semantic_matches", 0),
                    "semantic_match_rate": stats.get("semantic_match_rate", 0.0),
                    "avg_semantic_confidence": stats.get(
                        "avg_semantic_confidence", 0.0
                    ),
                }
            )
        else:
            report["semantic_matching_enabled"] = False

        return report

    def _save_json_report(self, report: Dict[str, Any], output_path: Path) -> None:
        """Save report to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def export_combined_summary(self) -> None:
        """Export combined summary of all runs."""
        self.excel_exporter.export_all_cases_summary()
