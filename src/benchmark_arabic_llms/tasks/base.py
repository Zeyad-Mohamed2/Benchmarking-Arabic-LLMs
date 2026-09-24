"""Base task interface defining the contract for all benchmark tasks."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


class BaseTask(ABC):
    """Abstract base class defining the contract for all benchmark tasks."""

    name: str = ""
    display_name: str = ""
    required_columns: List[str] = []
    default_dataset_path: Path
    default_prompt_template_path: Path
    judge_prompt_template_path: Optional[Path] = None

    def load_prompt_template(self, custom_template: Optional[str] = None) -> str:
        """Load default or custom prompt template."""
        if custom_template:
            return custom_template
        if not self.default_prompt_template_path.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {self.default_prompt_template_path}"
            )
        return self.default_prompt_template_path.read_text(encoding="utf-8")

    @abstractmethod
    def build_prompt(
        self, item: Dict[str, Any], template: Optional[str] = None
    ) -> Tuple[str, str]:
        """Build prompt and extract reference answer from a dataset item.

        Returns:
            Tuple of (prompt, reference)
        """
        pass

    @abstractmethod
    def evaluate(
        self, references: List[str], predictions: List[str]
    ) -> Dict[str, float]:
        """Compute evaluation metrics for the task."""
        pass

    @abstractmethod
    def get_primary_metric_key(self) -> str:
        """Return the primary metric name (e.g. 'Accuracy', 'ROUGE1', 'EM')."""
        pass
