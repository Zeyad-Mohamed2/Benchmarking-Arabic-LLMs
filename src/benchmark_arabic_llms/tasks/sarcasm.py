"""Sarcasm Detection benchmark task."""

from typing import Dict, List, Tuple, Any, Optional
from benchmark_arabic_llms.tasks.base import BaseTask
from benchmark_arabic_llms.tasks.registry import register_task
from benchmark_arabic_llms.config.data_paths import (
    SARCASM_DATA_CSV,
    SARCASM_PROMPT,
    SARCASM_JUDGE_PROMPT,
)
from benchmark_arabic_llms.evaluation.sarcasm import evaluate_sarcasm


@register_task("sarcasm")
class SarcasmTask(BaseTask):
    """Sarcasm Detection benchmark task."""

    name = "sarcasm"
    display_name = "Sarcasm Detection"
    required_columns = ["text", "sarcasm"]
    default_dataset_path = SARCASM_DATA_CSV
    default_prompt_template_path = SARCASM_PROMPT
    judge_prompt_template_path = SARCASM_JUDGE_PROMPT

    def build_prompt(
        self, item: Dict[str, Any], template: Optional[str] = None
    ) -> Tuple[str, str]:
        tpl = template or self.load_prompt_template()
        prompt = tpl.format(text=item.get("text", ""))
        reference = str(item.get("sarcasm", ""))
        return prompt, reference

    def evaluate(
        self, references: List[str], predictions: List[str]
    ) -> Dict[str, float]:
        return evaluate_sarcasm(references, predictions)

    def get_primary_metric_key(self) -> str:
        return "Accuracy"
