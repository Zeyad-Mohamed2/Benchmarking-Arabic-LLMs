from typing import List, Optional, Any
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import os
from sse_starlette.sse import EventSourceResponse

from benchmark_arabic_llms.core.enums import BenchmarkTask
from benchmark_arabic_llms.app.benchmark_orchestrator import BenchmarkOrchestrator
from benchmark_arabic_llms.config.data_paths import LOGS_DIR, EXCEL_DIR
from benchmark_arabic_llms.services.llm_client import OpenRouterClient, GroqClient
from google import genai

router = APIRouter()

class ConnectionTestRequest(BaseModel):
    provider: str
    api_key: str
    models: List[str]

class BenchmarkRequest(BaseModel):
    task: str
    provider: str
    api_key: str
    models: List[str]
    custom_prompt: Optional[str] = None
    number_of_samples: int = 10
    gemini_api_key: Optional[str] = None
    gemini_model_name: Optional[str] = None
    use_semantic_matching: bool = False
    enable_checkpoint_mode: bool = False
    checkpoint_interval: int = 50

@router.get("/setup")
def get_setup_info():
    """Returns available tasks and configuration metadata."""
    return {"tasks": BenchmarkTask.get_all()}

def _test_gemini_connection(api_key: str, model_name: str) -> tuple[bool, str]:
    try:
        client = genai.Client(api_key=api_key)
        client.models.generate_content(model=model_name, contents="Test")
        return True, "✅ Connection successful"
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)[:50]}"

def _test_openrouter_connection(api_key: str, model_name: str) -> tuple[bool, str]:
    try:
        client = OpenRouterClient(api_key=api_key, model=model_name)
        client.generate("Test", temperature=0.0)
        return True, "✅ Connection successful"
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)[:50]}"

def _test_groq_connection(api_key: str, model_name: str) -> tuple[bool, str]:
    try:
        client = GroqClient(api_key=api_key, model=model_name)
        client.generate("Test", temperature=0.0)
        return True, "✅ Connection successful"
    except Exception as e:
        return False, f"❌ Connection failed: {str(e)[:50]}"

@router.post("/test-connection")
def test_connection(request: ConnectionTestRequest):
    """Test API connection for given provider and models."""
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    if not request.models:
        raise HTTPException(status_code=400, detail="At least one model must be selected")
    
    results = {}
    all_success = True
    for model in request.models:
        if request.provider == "openrouter":
            success, message = _test_openrouter_connection(request.api_key, model)
        elif request.provider == "groq":
            success, message = _test_groq_connection(request.api_key, model)
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")
            
        results[model] = message
        if not success:
            all_success = False

    return {"success": all_success, "messages": results}

# Global state to track progress for SSE
benchmark_progress_queues = {}

@router.post("/run-benchmark")
async def run_benchmark_endpoint(
    task: str = Form(...),
    provider: str = Form(...),
    api_key: str = Form(...),
    models: str = Form(...), # Comma separated list
    custom_prompt: Optional[str] = Form(None),
    number_of_samples: int = Form(10),
    gemini_api_key: Optional[str] = Form(None),
    gemini_model_name: Optional[str] = Form(None),
    use_semantic_matching: bool = Form(False),
    enable_checkpoint_mode: bool = Form(False),
    checkpoint_interval: int = Form(50),
    dataset: Optional[UploadFile] = File(None)
):
    """Trigger a benchmark run. Returns an ID which can be used to listen to SSE events."""
    
    models_list = [m.strip() for m in models.split(",")]
    
    # Capture the current event loop to use in the background thread
    loop = asyncio.get_running_loop()

    # Generate unique run ID
    import uuid
    run_id = str(uuid.uuid4())
    benchmark_progress_queues[run_id] = asyncio.Queue()

    # Helper to post to the async queue from sync python thread
    queue = benchmark_progress_queues[run_id]
    def progress_callback(current: int, total: int, status: str):
        # Notify the asyncio queue from the sync thread safely
        loop.call_soon_threadsafe(
            queue.put_nowait, {"current": current, "total": total, "status": status}
        )

    dataset_content = None
    if dataset:
        import io

        class UploadedFileMock(io.BytesIO):
            def __init__(self, upload_file: UploadFile):
                content = upload_file.file.read()
                super().__init__(content)
                self.name = upload_file.filename or "uploaded_dataset.csv"

            def getvalue(self):
                return super().getvalue()

        dataset_content = UploadedFileMock(dataset)

    # Run orchestrator in a background thread to not block the main thread.
    def do_run():
        try:
            orchestrator = BenchmarkOrchestrator(LOGS_DIR, EXCEL_DIR)
            results = orchestrator.run_multiple(
                task=task,
                model_names=models_list,
                api_key=api_key,
                provider=provider,
                custom_prompt=custom_prompt,
                number_of_samples=number_of_samples,
                gemini_api_key=gemini_api_key,
                gemini_model_name=gemini_model_name,
                use_semantic_matching=use_semantic_matching,
                progress_callback=progress_callback,
                uploaded_dataset=dataset_content,
                enable_checkpoint_mode=enable_checkpoint_mode,
                checkpoint_interval=checkpoint_interval
            )
            # Indicate done
            loop.call_soon_threadsafe(
                 queue.put_nowait, {"done": True, "results": results}
            )
        except Exception as e:
            loop.call_soon_threadsafe(
                 queue.put_nowait, {"error": str(e)}
            )

    
    loop.run_in_executor(None, do_run)
    
    return {"run_id": run_id}

@router.get("/progress/{run_id}")
async def get_progress(run_id: str):
    """SSE endpoint to get updates on the benchmark run."""
    if run_id not in benchmark_progress_queues:
         raise HTTPException(status_code=404, detail="Run ID not found")
         
    queue = benchmark_progress_queues[run_id]

    async def event_generator():
        try:
            while True:
                msg = await queue.get()
                if "error" in msg:
                    yield {"event": "error", "data": msg["error"]}
                    break
                if "done" in msg:
                    import json
                    yield {"event": "done", "data": json.dumps(msg["results"])}
                    break
                
                import json
                yield {"event": "progress", "data": json.dumps(msg)}
        finally:
            benchmark_progress_queues.pop(run_id, None)

    return EventSourceResponse(event_generator())

@router.get("/download")
async def download_file(file_path: str):
    """Download a file by its absolute path."""
    from pathlib import Path

    if not file_path:
        raise HTTPException(status_code=400, detail="File path is required")
        
    target_path = Path(file_path).resolve()
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    # Ensure it's inside allowed directories
    allowed_dirs = [LOGS_DIR.resolve(), EXCEL_DIR.resolve()]
    is_allowed = any(
        target_path == d or target_path.is_relative_to(d)
        for d in allowed_dirs
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Access to this path is forbidden")
        
    return FileResponse(
        path=str(target_path), 
        filename=target_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/leaderboard")
async def get_leaderboard():
    """
    Read the leaderboard CSV files from data/leaderboard and return as JSON.
    Groups the results by task name.
    """
    import pandas as pd
    from pathlib import Path
    
    # Path is relative to where main.py runs (project root)
    leaderboard_dir = Path("data/leaderboard")
    
    if not leaderboard_dir.exists():
        return {"success": False, "error": "Leaderboard data directory not found"}
        
    results = {}
    try:
        for file in leaderboard_dir.glob("*_results.csv"):
            task_name = file.stem.replace("_results", "")
            df = pd.read_csv(file)
            
            # Remove 'Total' column
            if "Total" in df.columns:
                df = df.drop(columns=["Total"])
                
            # Implement Combined Score logic
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                # Calculate mean of all metrics for a combined score
                df["Combined_Score"] = df[numeric_cols].mean(axis=1).round(4)
            
            # Sort leaderboard from highest to lowest score
            sort_cols = []
            if task_name == "sarcasm":
                sort_cols = ["Combined_Score", "Accuracy", "F1"]
            else:
                sort_cols = ["Combined_Score", "Sem_Match", "BERTScore_F1"]
                
            available_sort_cols = [col for col in sort_cols if col in df.columns]
            if available_sort_cols:
                df = df.sort_values(by=available_sort_cols, ascending=False)
            
            # Clean up the dataframe (handle NaNs if any)
            df = df.fillna("")
            
            results[task_name] = df.to_dict(orient="records")
            
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


class LeaderboardPromoteRequest(BaseModel):
    task: str
    model: str
    scores: dict
    total_samples: int = 1000
    semantic_match_rate: Optional[float] = None


@router.post("/leaderboard/promote")
async def promote_to_leaderboard(request: LeaderboardPromoteRequest):
    """Promote or update a benchmarked model in the official leaderboard CSV."""
    import pandas as pd
    from pathlib import Path

    leaderboard_dir = Path("data/leaderboard")
    leaderboard_dir.mkdir(parents=True, exist_ok=True)

    task_map = {
        "qa": "question_answering",
        "question_answering": "question_answering",
        "summarization": "summarization",
        "sarcasm": "sarcasm",
    }
    canonical_task = task_map.get(request.task.lower(), request.task.lower())
    csv_path = leaderboard_dir / f"{canonical_task}_results.csv"

    scores = request.scores or {}
    clean_model_name = request.model.replace(":free", "")

    if canonical_task == "sarcasm":
        row_data = {
            "Model": clean_model_name,
            "Total": request.total_samples,
            "Accuracy": round(float(scores.get("Accuracy", scores.get("accuracy", 0.0))), 4),
            "F1": round(float(scores.get("F1", scores.get("f1", 0.0))), 4),
            "Precision": round(float(scores.get("Precision", scores.get("precision", 0.0))), 4),
            "Recall": round(float(scores.get("Recall", scores.get("recall", 0.0))), 4),
            "ROC_AUC": round(float(scores.get("ROC_AUC", scores.get("roc_auc", 0.0))), 4),
        }
    else:
        row_data = {
            "Model": clean_model_name,
            "Total": request.total_samples,
            "ROUGE1": round(float(scores.get("ROUGE1", scores.get("rouge1", 0.0))), 4),
            "ROUGEL": round(float(scores.get("ROUGEL", scores.get("rougeL", 0.0))), 4),
            "BLEU": round(float(scores.get("BLEU", scores.get("bleu", 0.0))), 4),
            "METEOR": round(float(scores.get("METEOR", scores.get("meteor", 0.0))), 4),
            "BERTScore_F1": round(float(scores.get("BERTScore", scores.get("bert_score", 0.0))), 4),
            "Sem_Match": round(float(request.semantic_match_rate or 0.0), 4),
        }

    try:
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            # Check if model already exists
            match_idx = df.index[df["Model"] == clean_model_name].tolist()
            if match_idx:
                for col, val in row_data.items():
                    if col in df.columns:
                        df.at[match_idx[0], col] = val
            else:
                df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        else:
            df = pd.DataFrame([row_data])

        df.to_csv(csv_path, index=False)
        return await get_leaderboard()
    except Exception as e:
        return {"success": False, "error": f"Failed to promote model to leaderboard: {e}"}

