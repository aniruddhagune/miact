import os
import datetime
import json
import threading
from backend.config.variables import DEBUG

class MIACTLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MIACTLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Use backend/debug as the storage location
        self.debug_folder = os.path.join("backend", "debug")
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)
        
        # Create a session-specific log file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.debug_folder, f"session_{timestamp}.log")
        self._initialized = True
        
        self.log("info", "GLOBAL", "Logger initialized. New session started.")

    def log(self, level, service, message, data=None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level.upper(),
            "service": service.upper(),
            "message": message
        }
        if data:
            log_entry["data"] = data

        # Write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")

        # If debug is enabled, also print to console
        if DEBUG or level.lower() in ["error", "warning"]:
            color = ""
            reset = "\033[0m"
            if level.lower() == "error":
                color = "\033[91m"  # Red
            elif level.lower() == "warning":
                color = "\033[93m"  # Yellow
            elif level.lower() == "debug":
                color = "\033[94m"  # Blue
            elif level.lower() == "info":
                color = "\033[92m"  # Green
            
            prefix = f"[{service.upper()}]"
            print(f"{color}{prefix:<12} [{level.upper()}] {message}{reset}")
            if data and DEBUG:
                try:
                    print(f"      Data: {json.dumps(data, indent=2)}")
                except:
                    print(f"      Data: {data}")

    def info(self, service, message, data=None):
        self.log("info", service, message, data)

    def error(self, service, message, data=None):
        self.log("error", service, message, data)

    def warning(self, service, message, data=None):
        self.log("warning", service, message, data)

    def debug(self, service, message, data=None):
        # Always log to file, but only print if DEBUG is True
        self.log("debug", service, message, data)

# Global logger instance
logger = MIACTLogger()
