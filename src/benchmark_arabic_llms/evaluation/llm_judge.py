"""benchmark_arabic_llms.evaluation.llm_judge

Gemini-based semantic matcher.

For QA specifically, the matcher can optionally receive the input example (question + passage
text) to judge correctness with respect to the passage, not just paraphrase similarity.
"""

import time
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional

import warnings
from google import genai

from benchmark_arabic_llms.config.data_paths import (
    QA_JUDGE_PROMPT,
    SARCASM_JUDGE_PROMPT,
    SUMMARIZATION_JUDGE_PROMPT,
)

# Silence the SyntaxWarning from the 'multiprocess' dependency in Python 3.14
warnings.filterwarnings("ignore", category=SyntaxWarning, module="multiprocess")


class SemanticMatcher:
    """Uses Gemini to evaluate semantic similarity between outputs."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash-lite",
        max_cache_size: int = 5000,
    ):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.max_cache_size = max(100, int(max_cache_size))
        self.cache: "OrderedDict[str, tuple[bool, str, float]]" = OrderedDict()
        self._load_judge_prompts()

    def check_semantic_match(
        self,
        output: str,
        reference: str,
        task_context: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, str, float]:
        """Check if output semantically matches reference."""
        cache_key = self._build_cache_key(output, reference, task_context, input_data)
        if cache_key in self.cache:
            self.cache.move_to_end(cache_key)
            return self.cache[cache_key]

        prompt = self._build_evaluation_prompt(output, reference, task_context, input_data)

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                result = self._parse_gemini_response(response.text)
                self._add_to_cache(cache_key, result)
                return result
            except Exception as e:
                if attempt < 2:
                    print(f"⚠️ Semantic matching attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
                    continue
                print(f"Warning: Semantic matching failed after 3 attempts: {e}")
                exact_match = output.strip() == reference.strip()
                return (exact_match, f"Fallback to exact match due to error: {e}", 0.5)

    def _build_cache_key(
        self,
        output: str,
        reference: str,
        task_context: Optional[str],
        input_data: Optional[Dict[str, Any]],
    ) -> str:
        """Build compact deterministic cache key to reduce memory pressure."""
        payload = {
            "task": task_context,
            "output": output,
            "reference": reference,
            "input": input_data or {},
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _add_to_cache(self, key: str, value: tuple[bool, str, float]) -> None:
        """Store cache item and evict oldest entries when cache is full."""
        self.cache[key] = value
        self.cache.move_to_end(key)
        while len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)

    def _load_judge_prompts(self) -> None:
        self.judge_prompts = {
            "question_answering": self._read_prompt_file(QA_JUDGE_PROMPT),
            "sarcasm": self._read_prompt_file(SARCASM_JUDGE_PROMPT),
            "summarization": self._read_prompt_file(SUMMARIZATION_JUDGE_PROMPT),
        }

    def _read_prompt_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: Could not load judge prompt from {path}: {e}")
            return ""

    def _build_evaluation_prompt(
        self,
        output: str,
        reference: str,
        task_context: Optional[str],
        input_data: Optional[Dict[str, Any]],
    ) -> str:
        template = self.judge_prompts.get(task_context, "")

        if not template:
            print(f"Warning: No judge prompt template found for task: {task_context}")
            return self._build_generic_prompt(output, reference, task_context)

        format_vars = {
            "output": output,
            "reference": reference,
        }

        if task_context == "question_answering" and input_data:
            format_vars["question"] = str(input_data.get("question", "")).strip()
            format_vars["passage"] = str(
                input_data.get("text", input_data.get("context", ""))
            ).strip()
        elif task_context in {"sarcasm", "summarization"} and input_data:
            format_vars["text"] = str(input_data.get("text", "")).strip()

        try:
            return template.format(**format_vars)
        except KeyError as e:
            print(f"Warning: Missing variable {e} in judge prompt template")
            return self._build_generic_prompt(output, reference, task_context)

    def _build_generic_prompt(
        self,
        output: str,
        reference: str,
        task_context: Optional[str],
    ) -> str:
        context_str = f"Task Context: {task_context}\n\n" if task_context else ""

        return f"""You are an expert evaluator. Judge if the output matches the reference semantically.

{context_str}Reference Answer:
{reference}

Model Output:
{output}

Instructions:
- Focus on semantic meaning, not exact wording
- Accept paraphrases and valid variations
- For classification tasks, focus only on the label
- Be generous with acceptable differences

Output format:
MATCH: [YES/NO]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [Brief explanation]"""

    def _parse_gemini_response(self, response_text: str) -> tuple[bool, str, float]:
        # Ensure we handle markdown blocks if Gemini wraps the response in ```
        clean_text = response_text.replace("```", "").strip()
        lines = clean_text.split("\n")

        match = False
        confidence = 0.5
        explanation = "Unable to parse response"

        for line in lines:
            line = line.strip()
            if line.startswith("MATCH:"):
                match_str = line.replace("MATCH:", "").strip().upper()
                match = "YES" in match_str
            elif line.startswith("CONFIDENCE:"):
                try:
                    conf_val = "".join(
                        c
                        for c in line.replace("CONFIDENCE:", "")
                        if c.isdigit() or c == "."
                    )
                    confidence = float(conf_val)
                except ValueError:
                    confidence = 0.5
            elif line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()

        return (match, explanation, confidence)