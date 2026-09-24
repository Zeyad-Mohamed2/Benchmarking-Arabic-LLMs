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
        return [task.value for task in cls]
