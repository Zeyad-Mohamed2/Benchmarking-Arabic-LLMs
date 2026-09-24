from typing import Dict, List
from benchmark_arabic_llms.evaluation.utils import (
    compute_text_generation_metrics,
    empty_text_metric_scores,
)

def evaluate_qa(
    references: List[str],
    predictions: List[str],
) -> Dict[str, float]:
    """Evaluate QA predictions with shared text-generation metrics."""
    valid_pairs = [
        (r, p) for r, p in zip(references, predictions)
        if r is not None and p is not None and str(r).strip() and str(p).strip()
    ]

    if not valid_pairs:
        return empty_text_metric_scores()

    refs = [r for r, _ in valid_pairs]
    hyps = [p for _, p in valid_pairs]
    return compute_text_generation_metrics(refs, hyps, include_bertscore=True)
