import re
import os
import warnings
import math
import logging
from collections import Counter
from statistics import fmean
from typing import Dict, List, Tuple

import sacrebleu
from bert_score import score as bertscore_score
from nltk.translate.meteor_score import single_meteor_score

# Suppress warnings from huggingface to avoid console clutter
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
os.environ["transformers_VERBOSITY"] = "error"

_DIACRITICS_RE = re.compile(r"[\u064B-\u0652]")
_ALEF_RE = re.compile(r"[إأآا]")
_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def empty_text_metric_scores() -> Dict[str, float]:
    """Return the empty/default score dictionary for text generation metrics."""
    return {
        "ROUGE1": 0.0,
        "ROUGEL": 0.0,
        "BLEU": 0.0,
        "METEOR": 0.0,
        "BERTScore": 0.0,
    }

def normalize_arabic(text):
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    text = str(text)
    text = _DIACRITICS_RE.sub('', text)
    text = _ALEF_RE.sub('ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ئ', 'ي', text)
    text = re.sub(r'ؤ', 'و', text)
    return text.strip()


def arabic_word_tokens(text: str) -> List[str]:
    """Tokenize text into Unicode word tokens suitable for Arabic metrics."""
    return _TOKEN_RE.findall(text or "")


def _f1_from_overlap(overlap: int, ref_len: int, hyp_len: int) -> float:
    if overlap <= 0 or ref_len <= 0 or hyp_len <= 0:
        return 0.0
    precision = overlap / hyp_len
    recall = overlap / ref_len
    return (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0


def _lcs_length(a: List[str], b: List[str]) -> int:
    if not a or not b:
        return 0
    # Classic DP for LCS with O(len(a) * len(b)) time and O(len(b)) memory.
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        curr = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[-1]


def rouge1_and_rougel_f1(reference: str, hypothesis: str) -> Tuple[float, float]:
    """Compute ROUGE-1 F1 and ROUGE-L F1 for a single reference/hypothesis pair."""
    ref_tokens = arabic_word_tokens(reference)
    hyp_tokens = arabic_word_tokens(hypothesis)

    if not ref_tokens or not hyp_tokens:
        return 0.0, 0.0

    ref_counts = Counter(ref_tokens)
    hyp_counts = Counter(hyp_tokens)
    unigram_overlap = sum((ref_counts & hyp_counts).values())
    rouge1_f1 = _f1_from_overlap(unigram_overlap, len(ref_tokens), len(hyp_tokens))

    lcs = _lcs_length(ref_tokens, hyp_tokens)
    rougel_f1 = _f1_from_overlap(lcs, len(ref_tokens), len(hyp_tokens))

    return float(rouge1_f1), float(rougel_f1)


def compute_text_generation_metrics(
    references: List[str],
    predictions: List[str],
    include_bertscore: bool = True,
) -> Dict[str, float]:
    """Compute shared text-generation metrics for QA and summarization.

    Inputs are expected to be pre-cleaned by the caller.
    """
    if not references or not predictions:
        return empty_text_metric_scores()

    pair_count = min(len(references), len(predictions))
    if pair_count <= 0:
        return empty_text_metric_scores()

    all_refs = [normalize_arabic(r) for r in references[:pair_count]]
    all_hyps = [normalize_arabic(p) for p in predictions[:pair_count]]

    r1, rl, corpus_bleu, corpus_meteor, bert_score_mean = 0.0, 0.0, 0.0, 0.0, 0.0

    try:
        rouge1_scores = []
        rougeL_scores = []
        for ref, hyp in zip(all_refs, all_hyps):
            r1_pair, rl_pair = rouge1_and_rougel_f1(ref, hyp)
            rouge1_scores.append(r1_pair)
            rougeL_scores.append(rl_pair)
        r1 = float(fmean(rouge1_scores)) if rouge1_scores else 0.0
        rl = float(fmean(rougeL_scores)) if rougeL_scores else 0.0
    except Exception as e:
        logging.warning(f"ROUGE computation failed: {e}")

    try:
        corpus_bleu = float(sacrebleu.corpus_bleu(all_hyps, [all_refs]).score / 100.0)
    except Exception as e:
        logging.warning(f"BLEU computation failed: {e}")

    try:
        meteor_scores = []
        for ref, hyp in zip(all_refs, all_hyps):
            ref_tokens = arabic_word_tokens(ref)
            hyp_tokens = arabic_word_tokens(hyp)
            meteor_scores.append(float(single_meteor_score(ref_tokens, hyp_tokens)))
        corpus_meteor = float(fmean(meteor_scores)) if meteor_scores else 0.0
    except Exception as e:
        logging.warning(f"METEOR computation failed: {e}")

    if include_bertscore:
        try:
            _, _, f1 = bertscore_score(all_hyps, all_refs, lang="ar", verbose=False)
            bert_score_mean = float(f1.mean().item())
        except Exception as e:
            logging.warning(f"BERTScore computation failed: {e}")

    return {
        "ROUGE1": float(r1),
        "ROUGEL": float(rl),
        "BLEU": float(corpus_bleu),
        "METEOR": float(corpus_meteor),
        "BERTScore": float(bert_score_mean),
    }

