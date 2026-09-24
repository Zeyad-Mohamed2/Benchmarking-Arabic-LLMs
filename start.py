import subprocess
import sys
import os
import time

def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    print("🚀 Starting FastAPI backend on port 8000...")
    backend = subprocess.Popen(
        ["poetry", "run", "python", "src/benchmark_arabic_llms/main.py", "--mode", "api", "--port", "8000"],
        cwd=root_dir,
        shell=True
    )

    # Let the backend initialize
    time.sleep(2)

    print("🚀 Starting Vite React frontend...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )

    print("\n✅ Application is running!")
    print("➡️  Frontend: http://localhost:5173")
    print("➡️  Backend API: http://localhost:8000/api/setup")
    print("Press Ctrl+C to stop both servers.\n")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down processes...")
        backend.terminate()
        frontend.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()