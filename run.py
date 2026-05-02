import subprocess
import sys
import os
import time
import argparse
import shutil

def run_all():
    parser = argparse.ArgumentParser(description="MIACT Runner with Service-Specific Debugging")
    parser.add_argument("--services", type=str, default="*", 
                        help="Comma-separated list of services to debug (e.g., SEARCH,NLP,DATABASE). Default is '*' (all).")
    parser.add_argument("--log-selected-only", action="store_true", 
                        help="If set, only the selected services will be written to the session log file. Default is to log everything to file.")
    
    args = parser.parse_args()

    print("🚀 Starting MIACT Full Stack...")
    
    # Set environment variables for the backend to pick up
    env = os.environ.copy()
    env["MIACT_SERVICES"] = args.services
    env["MIACT_LOG_ALL"] = "False" if args.log_selected_only else "True"

    print(f"🔍 Debug Services: {args.services}")
    print(f"📝 Log All to File: {'No' if args.log_selected_only else 'Yes'}")

    # Determine backend command based on available tools
    uv_path = shutil.which("uv")
    if uv_path:
        print("🛠️  Using 'uv' for backend execution")
        backend_cmd = [
            "uv", "run", "python",
            "-m", "uvicorn",
            "backend.main:app",
            "--reload",
            "--reload-dir", "backend",
            "--reload-exclude", "*.log",
            "--port", "8000",
            "--loop", "none"
        ]
    else:
        # Fallback to local virtual environment or current python
        venv_python = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join("venv", "bin", "python")
        if os.path.exists(venv_python):
            python_exe = venv_python
            print(f"🐍 Using virtual environment python: {python_exe}")
        else:
            python_exe = sys.executable
            print(f"🐍 Using current python: {python_exe}")
        
        backend_cmd = [
            python_exe,
            "-m", "uvicorn",
            "backend.main:app",
            "--reload",
            "--reload-dir", "backend",
            "--reload-exclude", "*.log",
            "--port", "8000",
            "--loop", "none"
        ]
    
    print("📦 Launching Backend on http://127.0.0.1:8000")
    backend_proc = subprocess.Popen(backend_cmd, env=env)

    # 2. Start Frontend (Vite)
    print("🎨 Launching Frontend...")
    frontend_proc = subprocess.Popen(
        "npm run dev",
        cwd="frontend",
        shell=True
    )

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("❌ Backend process terminated.")
                break
            if frontend_proc.poll() is not None:
                print("❌ Frontend process terminated.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MIACT...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    run_all()
