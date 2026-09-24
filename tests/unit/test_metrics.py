"""Unit tests for task evaluation metrics."""

from benchmark_arabic_llms.evaluation.qa import evaluate_qa
from benchmark_arabic_llms.evaluation.sarcasm import evaluate_sarcasm
from benchmark_arabic_llms.evaluation.utils import rouge1_and_rougel_f1


def test_rouge1_and_rougel_exact_match():
    ref = "القاهرة عاصمة جمهورية مصر العربية"
    hyp = "القاهرة عاصمة جمهورية مصر العربية"
    r1, rl = rouge1_and_rougel_f1(ref, hyp)
    assert abs(r1 - 1.0) < 1e-4
    assert abs(rl - 1.0) < 1e-4


def test_rouge1_partial_overlap():
    ref = "الذكاء الاصطناعي يغير العالم بسرعة"
    hyp = "الذكاء الاصطناعي يغير المستقبل"
    r1, rl = rouge1_and_rougel_f1(ref, hyp)
    assert 0.0 < r1 < 1.0
    assert 0.0 < rl < 1.0


def test_rouge_empty_strings():
    r1, rl = rouge1_and_rougel_f1("", "")
    assert r1 == 0.0
    assert rl == 0.0


def test_qa_exact_match_and_f1():
    references = ["واشنطن العاصمة", "القاهرة"]
    predictions = ["واشنطن العاصمة", "مدينة القاهرة"]
    scores = evaluate_qa(references, predictions)

    # First is exact match, second is partial token overlap
    assert "Accuracy" in scores
    assert "EM" in scores
    assert "F1" in scores
    assert scores["EM"] == 0.5  # 1 of 2 is exact
    assert scores["F1"] > 0.5   # both have high overlap


def test_sarcasm_metrics():
    references = ["ساخر", "غير ساخر", "ساخر", "غير ساخر"]
    predictions = ["ساخر", "غير ساخر", "غير ساخر", "غير ساخر"]
    scores = evaluate_sarcasm(references, predictions)

    assert "Accuracy" in scores
    assert "F1" in scores
    assert "Precision" in scores
    assert "Recall" in scores
    assert scores["Accuracy"] == 0.75
