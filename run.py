import subprocess
import sys
import os
import time
import argparse

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

    # 1. Start Backend (FastAPI)
    backend_cmd = [
        os.path.join("venv", "Scripts", "python.exe"),
        "-m", "uvicorn",
        "backend.main:app",
        "--reload",
        "--port", "8000"
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
