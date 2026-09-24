"""Text Summarization benchmark task."""

from typing import Dict, List, Tuple, Any, Optional
from benchmark_arabic_llms.tasks.base import BaseTask
from benchmark_arabic_llms.tasks.registry import register_task
from benchmark_arabic_llms.config.data_paths import (
    SUMMARIZATION_DATA_CSV,
    SUMMARIZATION_PROMPT,
    SUMMARIZATION_JUDGE_PROMPT,
)
from benchmark_arabic_llms.evaluation.summarization import evaluate_summaries


@register_task("summarization")
class SummarizationTask(BaseTask):
    """Text Summarization benchmark task."""

    name = "summarization"
    display_name = "Text Summarization"
    required_columns = ["text", "summary"]
    default_dataset_path = SUMMARIZATION_DATA_CSV
    default_prompt_template_path = SUMMARIZATION_PROMPT
    judge_prompt_template_path = SUMMARIZATION_JUDGE_PROMPT

    def build_prompt(
        self, item: Dict[str, Any], template: Optional[str] = None
    ) -> Tuple[str, str]:
        tpl = template or self.load_prompt_template()
        prompt = tpl.format(text=item.get("text", ""))
        reference = item.get("summary", "")
        return prompt, reference

    def evaluate(
        self, references: List[str], predictions: List[str]
    ) -> Dict[str, float]:
        return evaluate_summaries(references, predictions)

    def get_primary_metric_key(self) -> str:
        return "ROUGE1"
