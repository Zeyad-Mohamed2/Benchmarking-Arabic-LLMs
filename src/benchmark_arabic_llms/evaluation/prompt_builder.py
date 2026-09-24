"""
This file defines the PromptBuilder class, which constructs task-specific prompts and extracts reference answers.
It supports summarization, QA, and sarcasm detection tasks using flexible templates for each type.
"""

from typing import Dict, Tuple
from benchmark_arabic_llms.core.enums import BenchmarkTask


class PromptBuilder:
    """Builds prompts and extracts references for different tasks."""

    def __init__(self, template: str, task: BenchmarkTask):
        self.template = template
        self.task = task

    def build(self, item: Dict) -> Tuple[str, str]:
        """Build prompt and extract reference based on task type."""
        builders = {
            BenchmarkTask.SUMMARIZATION: self._build_summarization,
            BenchmarkTask.QA: self._build_qa,
            BenchmarkTask.SARCASM: self._build_sarcasm,
        }

        builder = builders.get(self.task)
        if not builder:
            raise ValueError(f"Unknown task: {self.task}")

        return builder(item)

    def _build_summarization(self, item: Dict) -> Tuple[str, str]:
        prompt = self.template.format(text=item.get("text", ""))
        reference = item.get("summary", "")
        return prompt, reference

    def _build_qa(self, item: Dict) -> Tuple[str, str]:
        prompt = self.template.format(
            text=item.get("text", "") or item.get("context", ""),
            question=item.get("question", ""),
        )
        reference = item.get("answer", "")
        return prompt, reference

    def _build_sarcasm(self, item: Dict) -> Tuple[str, str]:
        prompt = self.template.format(text=item.get("text", ""))
        reference = item.get("sarcasm", "")
        return prompt, reference
