"""
This file evaluates text summarization quality using multiple metrics.
It computes ROUGE-1, ROUGE-L, BLEU, METEOR, and BERTScore on the corpus level for predicted and reference summaries.
"""

from typing import List, Dict
from benchmark_arabic_llms.evaluation.utils import (
    compute_text_generation_metrics,
    empty_text_metric_scores,
)


def evaluate_summaries(
    references: List[str], predictions: List[str]
) -> Dict[str, float]:
    """Compute summarization metrics via the shared text-generation utility."""

    valid_pairs = [
        (r, p) for r, p in zip(references, predictions)
        if r is not None and p is not None and str(r).strip() and str(p).strip()
    ]
    if not valid_pairs:
        return empty_text_metric_scores()

    refs = [r for r, _ in valid_pairs]
    hyps = [p for _, p in valid_pairs]
    return compute_text_generation_metrics(refs, hyps, include_bertscore=True)
