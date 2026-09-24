"""
This file defines the Evaluator class, responsible for scoring model predictions.
It routes evaluation to task-specific modules (summarization, QA, sarcasm) after cleaning and validating reference-prediction pairs.
"""

from typing import Dict, Any, List
from benchmark_arabic_llms.core.enums import BenchmarkTask
from benchmark_arabic_llms.evaluation import qa as eval_qa
from benchmark_arabic_llms.core.exceptions import EvaluationError
from benchmark_arabic_llms.evaluation import sarcasm as eval_sarcasm
from benchmark_arabic_llms.evaluation import summarization as eval_summarization


class Evaluator:
    """Evaluates predictions against references."""

    def __init__(self, task: BenchmarkTask):
        self.task = task

    def evaluate(self, references: List[str], predictions: List[str]) -> Dict[str, Any]:
        """Evaluate predictions against references."""
        if not references or not predictions:
            raise EvaluationError("Empty references or predictions")

        cleaned_refs, cleaned_preds = self._clean_data(references, predictions)

        if not cleaned_refs or not cleaned_preds:
            raise EvaluationError("No valid data after cleaning")

        evaluators = {
            BenchmarkTask.SUMMARIZATION: eval_summarization.evaluate_summaries,
            BenchmarkTask.QA: eval_qa.evaluate_qa,
            BenchmarkTask.SARCASM: eval_sarcasm.evaluate_sarcasm,
        }

        evaluator_fn = evaluators.get(self.task)
        if not evaluator_fn:
            raise EvaluationError(f"No evaluator for task: {self.task}")

        try:
            return evaluator_fn(cleaned_refs, cleaned_preds)
        except Exception as e:
            raise EvaluationError(f"Evaluation failed: {e}")

    def _clean_data(
        self, references: List[Any], predictions: List[Any]
    ) -> tuple[List[str], List[str]]:
        """Clean and convert data to strings, removing empty pairs."""
        cleaned_refs = []
        cleaned_preds = []

        for ref, pred in zip(references, predictions):
            ref_str = str(ref).strip() if ref is not None else ""
            pred_str = str(pred).strip() if pred is not None else ""

            if ref_str and pred_str:
                cleaned_refs.append(ref_str)
                cleaned_preds.append(pred_str)

        return cleaned_refs, cleaned_preds
