from typing import Dict, List
from collections import Counter
from statistics import fmean
from benchmark_arabic_llms.evaluation.utils import (
    compute_text_generation_metrics,
    normalize_arabic,
    arabic_word_tokens,
    _f1_from_overlap,
)


def evaluate_qa(
    references: List[str],
    predictions: List[str],
) -> Dict[str, float]:
    """Evaluate QA predictions with Exact Match, token F1, and shared text-generation metrics."""
    valid_pairs = [
        (r, p) for r, p in zip(references, predictions)
        if r is not None and p is not None and str(r).strip() and str(p).strip()
    ]

    if not valid_pairs:
        return {
            "Accuracy": 0.0,
            "EM": 0.0,
            "F1": 0.0,
            "ROUGE1": 0.0,
            "ROUGEL": 0.0,
            "BLEU": 0.0,
            "METEOR": 0.0,
            "BERTScore": 0.0,
        }

    refs = [r for r, _ in valid_pairs]
    hyps = [p for _, p in valid_pairs]

    # Exact Match / Accuracy
    em_list = [
        1.0 if normalize_arabic(r) == normalize_arabic(h) else 0.0
        for r, h in zip(refs, hyps)
    ]
    em_score = float(fmean(em_list)) if em_list else 0.0

    # Token overlap F1 (SQuAD-style)
    f1_list = []
    for r, h in zip(refs, hyps):
        r_toks = arabic_word_tokens(normalize_arabic(r))
        h_toks = arabic_word_tokens(normalize_arabic(h))
        if not r_toks or not h_toks:
            f1_list.append(0.0)
        else:
            overlap = sum((Counter(r_toks) & Counter(h_toks)).values())
            f1_list.append(_f1_from_overlap(overlap, len(r_toks), len(h_toks)))
    f1_score = float(fmean(f1_list)) if f1_list else 0.0

    gen_metrics = compute_text_generation_metrics(refs, hyps, include_bertscore=True)

    result = {
        "Accuracy": em_score,
        "EM": em_score,
        "F1": f1_score,
    }
    result.update(gen_metrics)
    return result

