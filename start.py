import subprocess
import sys
import os
import time


def kill_process_tree(proc: subprocess.Popen | None):
    """Terminates process and all its children across platforms."""
    if proc is None:
        return
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass
    else:
        try:
            proc.terminate()
        except Exception:
            pass


def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print("🚀 Starting FastAPI backend on port 8000...")
    # Use poetry run or current python interpreter
    backend_cmd = (
        ["poetry", "run", "python", "src/benchmark_arabic_llms/main.py", "--mode", "api", "--port", "8000"]
    )
    backend = subprocess.Popen(backend_cmd, cwd=root_dir, shell=True)

    # Let the backend initialize
    time.sleep(2)

    print("🚀 Starting Vite React frontend...")
    frontend = subprocess.Popen(["npm", "run", "dev"], cwd=frontend_dir, shell=True)

    print("\n✅ Application is running!")
    print("➡️  Frontend: http://localhost:5173")
    print("➡️  Backend API: http://localhost:8000/api/setup")
    print("Press Ctrl+C to stop both servers.\n")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down processes...")
        kill_process_tree(backend)
        kill_process_tree(frontend)
        sys.exit(0)


if __name__ == "__main__":
    main()