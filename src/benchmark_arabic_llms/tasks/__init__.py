"""Tasks module with dynamic auto-registration."""

from benchmark_arabic_llms.tasks.base import BaseTask
from benchmark_arabic_llms.tasks.registry import TaskRegistry, register_task
from benchmark_arabic_llms.tasks.question_answering import QuestionAnsweringTask
from benchmark_arabic_llms.tasks.summarization import SummarizationTask
from benchmark_arabic_llms.tasks.sarcasm import SarcasmTask

__all__ = [
    "BaseTask",
    "TaskRegistry",
    "register_task",
    "QuestionAnsweringTask",
    "SummarizationTask",
    "SarcasmTask",
]
