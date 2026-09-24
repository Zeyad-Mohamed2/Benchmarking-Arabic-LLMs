"""
This file defines an enumeration of all supported benchmark tasks.
It standardizes task names (summarization, QA, sarcasm) and provides a helper method to list them.
"""

from enum import Enum


class BenchmarkTask(str, Enum):
    """Enumeration of supported benchmark tasks."""

    SUMMARIZATION = "summarization"
    QA = "question_answering"
    SARCASM = "sarcasm"

    @classmethod
    def get_all(cls):
        try:
            from benchmark_arabic_llms.tasks.registry import TaskRegistry
            import benchmark_arabic_llms.tasks  # noqa: F401
            names = TaskRegistry.list_names()
            if names:
                return names
        except Exception:
            pass
        return [task.value for task in cls]
