from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from benchmark_arabic_llms.api.routes import benchmark_router

app = FastAPI(title="Benchmark Arabic LLMs API", version="0.1.0")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(benchmark_router.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
