"""Unit tests for the TaskRegistry and BaseTask contract."""

import pytest
from benchmark_arabic_llms.tasks.registry import TaskRegistry, register_task
from benchmark_arabic_llms.tasks.base import BaseTask


def test_registry_contains_core_tasks():
    names = TaskRegistry.list_names()
    assert "question_answering" in names
    assert "summarization" in names
    assert "sarcasm" in names


def test_task_get_and_properties():
    qa = TaskRegistry.get("question_answering")
    assert qa.name == "question_answering"
    assert "text" in qa.required_columns
    assert "question" in qa.required_columns
    assert "answer" in qa.required_columns

    sum_task = TaskRegistry.get("summarization")
    assert sum_task.name == "summarization"
    assert "text" in sum_task.required_columns
    assert "summary" in sum_task.required_columns

    sarc_task = TaskRegistry.get("sarcasm")
    assert sarc_task.name == "sarcasm"
    assert "text" in sarc_task.required_columns
    assert "sarcasm" in sarc_task.required_columns


def test_custom_task_registration():
    @register_task("dummy_test_task")
    class DummyTask(BaseTask):
        display_name = "Dummy Test Task"
        required_columns = ["text", "label"]

        def build_prompt(self, item, template=None):
            return f"Prompt: {item.get('text')}", item.get("label")

        def evaluate(self, references, predictions):
            return {"Accuracy": 1.0}

        def get_primary_metric_key(self):
            return "Accuracy"

    assert TaskRegistry.is_registered("dummy_test_task")
    dummy = TaskRegistry.get("dummy_test_task")
    prompt, ref = dummy.build_prompt({"text": "تجربة", "label": "1"})
    assert prompt == "Prompt: تجربة"
    assert ref == "1"
    assert dummy.evaluate(["1"], ["1"])["Accuracy"] == 1.0
