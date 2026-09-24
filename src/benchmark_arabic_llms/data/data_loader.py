"""
This file handles loading datasets and prompt templates for benchmark tasks.
It validates file formats, ensures required columns exist, and extracts structured data for summarization, QA, or sarcasm benchmarks.
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from benchmark_arabic_llms.core.enums import BenchmarkTask
from benchmark_arabic_llms.core.exceptions import DataLoadError


class DataLoader:
    """Handles loading of datasets from CSV files or uploaded files."""

    def load_dataset(
        self, path: Path, task: BenchmarkTask, limit: int = None
    ) -> List[Dict]:
        """Load dataset from CSV file."""
        try:
            df = self._read_csv(path, limit)
            return self._extract_data_by_task(df, task)
        except Exception as e:
            raise DataLoadError(f"Failed to load dataset from {path}: {e}")

    def load_uploaded_dataset(
        self, uploaded_file: Any, task: BenchmarkTask, limit: int = None
    ) -> List[Dict]:
        """Load dataset from uploaded file (Streamlit UploadedFile object).

        Args:
            uploaded_file: Streamlit UploadedFile object
            task: Benchmark task type
            limit: Optional row limit

        Returns:
            List of dictionaries containing the dataset
        """
        try:
            # Determine file type from name
            file_name = uploaded_file.name.lower()

            if file_name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, encoding="utf-8", nrows=limit)
            elif file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file, nrows=limit)
            else:
                raise DataLoadError(f"Unsupported file format: {file_name}")

            return self._extract_data_by_task(df, task)

        except Exception as e:
            raise DataLoadError(f"Failed to load uploaded dataset: {e}")

    def _read_csv(self, path: Path, limit: int = None) -> pd.DataFrame:
        """Read CSV file with optional row limit."""
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        return pd.read_csv(path, encoding="utf-8", nrows=limit)

    def _extract_data_by_task(
        self, df: pd.DataFrame, task: BenchmarkTask
    ) -> List[Dict]:
        """Extract relevant columns based on task type.

        Validates that the dataframe contains the required columns for the task.
        """
        column_map = {
            BenchmarkTask.SUMMARIZATION: ["text", "summary"],
            BenchmarkTask.QA: ["text", "question", "answer"],
            BenchmarkTask.SARCASM: ["text", "sarcasm"],
        }

        required_columns = column_map.get(task)
        if not required_columns:
            raise DataLoadError(f"Unknown task: {task}")

        # Check if required columns exist in the dataframe
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise DataLoadError(
                f"Dataset is missing required columns: {list(missing_columns)}. "
                f"Required columns for {task.value}: {required_columns}. "
                f"Found columns: {list(df.columns)}"
            )

        # Extract only the required columns
        data = df[required_columns].to_dict(orient="records")

        if not data:
            raise DataLoadError("No valid data loaded from dataset")

        return data


class PromptTemplateLoader:
    """Handles loading of prompt templates."""

    @staticmethod
    def load(path: Path) -> str:
        """Load prompt template from file."""
        if not path.exists():
            raise FileNotFoundError(f"Prompt template not found: {path}")
        return path.read_text(encoding="utf-8")
