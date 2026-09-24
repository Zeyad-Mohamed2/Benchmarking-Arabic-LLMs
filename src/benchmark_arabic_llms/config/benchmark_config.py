"""
This file defines configuration handling for benchmark cases.
It manages dataset and prompt template paths for summarization, QA, and sarcasm tasks through a configurable ConfigManager.
"""

from pathlib import Path
from typing import Tuple
from dataclasses import dataclass

from benchmark_arabic_llms.config.data_paths import (
    SUMMARIZATION_DATA_CSV,
    QA_DATA_CSV,
    SARCASM_DATA_CSV,
    SUMMARIZATION_PROMPT,
    QA_PROMPT,
    SARCASM_PROMPT,
)


@dataclass
class BenchmarkConfig:
    """Configuration data class for benchmark settings."""

    case: str
    dataset_path: Path
    prompt_template_path: Path


class ConfigManager:
    """Handles configuration loading, validation, and path resolution."""

    CASE_PATHS = {
        "summarization": {
            "dataset": SUMMARIZATION_DATA_CSV,
            "prompt_template": SUMMARIZATION_PROMPT,
        },
        "question_answering": {
            "dataset": QA_DATA_CSV,
            "prompt_template": QA_PROMPT,
        },
        "sarcasm": {
            "dataset": SARCASM_DATA_CSV,
            "prompt_template": SARCASM_PROMPT,
        },
    }

    VALID_CASES = set(CASE_PATHS.keys())

    @classmethod
    def create(cls, case: str) -> BenchmarkConfig:
        """Create BenchmarkConfig directly from case name (ignore YAML/API keys)."""
        case = case.lower()

        if case not in cls.VALID_CASES:
            raise ValueError(
                f"Invalid case: {case}. Must be one of {sorted(cls.VALID_CASES)}"
            )

        dataset_path, prompt_template_path = cls._resolve_paths(case)

        return BenchmarkConfig(
            case=case,
            dataset_path=dataset_path,
            prompt_template_path=prompt_template_path,
        )

    @classmethod
    def _resolve_paths(cls, case: str) -> Tuple[Path, Path]:
        """Resolve dataset and prompt template paths for a given case."""
        dataset_path = cls.CASE_PATHS[case]["dataset"]
        prompt_template_path = cls.CASE_PATHS[case]["prompt_template"]

        return Path(dataset_path), Path(prompt_template_path)

