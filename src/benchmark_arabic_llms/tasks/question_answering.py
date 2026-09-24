"""Question Answering benchmark task."""

from typing import Dict, List, Tuple, Any, Optional
from benchmark_arabic_llms.tasks.base import BaseTask
from benchmark_arabic_llms.tasks.registry import register_task
from benchmark_arabic_llms.config.data_paths import (
    QA_DATA_CSV,
    QA_PROMPT,
    QA_JUDGE_PROMPT,
)
from benchmark_arabic_llms.evaluation.qa import evaluate_qa


@register_task("question_answering")
class QuestionAnsweringTask(BaseTask):
    """Question Answering benchmark task."""

    name = "question_answering"
    display_name = "Question Answering"
    required_columns = ["text", "question", "answer"]
    default_dataset_path = QA_DATA_CSV
    default_prompt_template_path = QA_PROMPT
    judge_prompt_template_path = QA_JUDGE_PROMPT

    def build_prompt(
        self, item: Dict[str, Any], template: Optional[str] = None
    ) -> Tuple[str, str]:
        tpl = template or self.load_prompt_template()
        prompt = tpl.format(
            text=item.get("text", "") or item.get("context", ""),
            question=item.get("question", ""),
        )
        reference = item.get("answer", "")
        return prompt, reference

    def evaluate(
        self, references: List[str], predictions: List[str]
    ) -> Dict[str, float]:
        return evaluate_qa(references, predictions)

    def get_primary_metric_key(self) -> str:
        return "Accuracy"
