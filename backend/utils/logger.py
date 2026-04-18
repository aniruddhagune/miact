import os
import datetime
import json
import threading
import backend.config.variables as _vars

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
        service_upper = service.upper()
        
        # 1. Determine if we should log to file
        # We log to file if LOG_ALL_TO_FILE is True OR if this service is in DEBUG_SERVICES
        is_service_enabled = "*" in _vars.DEBUG_SERVICES or service_upper in _vars.DEBUG_SERVICES
        
        should_log_to_file = _vars.LOG_ALL_TO_FILE or is_service_enabled

        if should_log_to_file:
            log_entry = {
                "timestamp": timestamp,
                "level": level.upper(),
                "service": service_upper,
                "message": message
            }
            if data:
                log_entry["data"] = data

            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                print(f"Failed to write to log file: {e}")

        # 2. Determine if we should print to console
        # We print if (DEBUG is True AND service is enabled) OR it's an error/warning
        should_print = (_vars.DEBUG and is_service_enabled) or level.lower() in ["error", "warning"]

        if should_print:
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
            
            prefix = f"[{service_upper}]"
            print(f"{color}{prefix:<12} [{level.upper()}] {message}{reset}")
            if data and _vars.DEBUG:
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
        self.log("debug", service, message, data)

# Global logger instance
logger = MIACTLogger()
