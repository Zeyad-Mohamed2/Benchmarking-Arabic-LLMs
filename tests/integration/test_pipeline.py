"""Integration tests for benchmark pipeline with Mock LLM."""

from pathlib import Path
from benchmark_arabic_llms.evaluation.benchmark_runner import BenchmarkRunner
from benchmark_arabic_llms.core.enums import BenchmarkTask


def test_pipeline_qa_end_to_end(tmp_path, mock_llm_client, sample_qa_data):
    runner = BenchmarkRunner(
        client=mock_llm_client,
        task=BenchmarkTask.QA,
        prompt_template="السياق: {text}\nالسؤال: {question}\nالإجابة:",
        log_dir=tmp_path / "logs",
        clear_log=True,
    )

    runner.process_examples(sample_qa_data)
    stats = runner.get_stats()
    scores = runner.evaluate()

    assert stats["n_examples"] == 2
    assert stats["n_errors"] == 0
    assert stats["api_success_rate"] == 1.0
    assert "Accuracy" in scores or "EM" in scores


def test_pipeline_sarcasm_end_to_end(tmp_path, mock_llm_client, sample_sarcasm_data):
    runner = BenchmarkRunner(
        client=mock_llm_client,
        task=BenchmarkTask.SARCASM,
        prompt_template="حدد هل النص التالي ساخر أم غير ساخر: {text}",
        log_dir=tmp_path / "logs",
        clear_log=True,
    )

    runner.process_examples(sample_sarcasm_data)
    stats = runner.get_stats()
    scores = runner.evaluate()

    assert stats["n_examples"] == 2
    assert stats["n_errors"] == 0
    assert "Accuracy" in scores
