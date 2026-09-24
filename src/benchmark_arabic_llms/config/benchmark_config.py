"""
This file defines configuration handling for benchmark cases.
It manages dataset and prompt template paths for summarization, QA, and sarcasm tasks through a configurable ConfigManager.
"""

from pathlib import Path
from typing import Tuple
from dataclasses import dataclass

from benchmark_arabic_llms.tasks.registry import TaskRegistry
import benchmark_arabic_llms.tasks  # noqa: F401 - ensure auto-registration


@dataclass
class BenchmarkConfig:
    """Configuration data class for benchmark settings."""

    case: str
    dataset_path: Path
    prompt_template_path: Path


class ConfigManager:
    """Handles configuration loading, validation, and path resolution via TaskRegistry."""

    @classmethod
    def create(cls, case: str) -> BenchmarkConfig:
        """Create BenchmarkConfig directly from task name."""
        task_name = str(case).lower()

        if not TaskRegistry.is_registered(task_name):
            raise ValueError(
                f"Invalid case: {case}. Must be one of {TaskRegistry.list_names()}"
            )

        task = TaskRegistry.get(task_name)

        return BenchmarkConfig(
            case=task_name,
            dataset_path=task.default_dataset_path,
            prompt_template_path=task.default_prompt_template_path,
        )

    @classmethod
    def _resolve_paths(cls, case: str) -> Tuple[Path, Path]:
        """Resolve dataset and prompt template paths for a given case."""
        task = TaskRegistry.get(str(case).lower())
        return task.default_dataset_path, task.default_prompt_template_path


