import os
import datetime
import json
import threading
import traceback
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
        
        # Create a session-specific log file + a "latest.log"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.debug_folder, f"session_{timestamp}.log")
        self.latest_log = os.path.join(self.debug_folder, "latest.log")
        
        # Synchronous logging for now to ensure reliability on low-end system
        # No background thread to avoid missing logs on crash
        
        self._initialized = True
        self.info("GLOBAL", "--- MIACT Logger Initialized (SYNC MODE) ---")

    def _write_to_file(self, entry):
        try:
            msg = json.dumps(entry) + "\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(msg)
                f.flush()
                os.fsync(f.fileno()) # Force write to physical disk
            with open(self.latest_log, "a", encoding="utf-8") as f:
                f.write(msg)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"CRITICAL: Logger write failed: {e}")

    def log(self, level, service, message, data=None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        service_upper = service.upper()
        level_upper = level.upper()
        
        # Automatically capture stack trace for errors if not provided
        if level_upper == "ERROR" and not data:
            stack = traceback.format_exc()
            if stack and "NoneType: None" not in stack:
                data = {"traceback": stack.splitlines()}

        # 1. File logging
        is_service_enabled = "*" in _vars.DEBUG_SERVICES or service_upper in _vars.DEBUG_SERVICES
        should_log_to_file = _vars.LOG_ALL_TO_FILE or is_service_enabled

        if should_log_to_file:
            log_entry = {
                "timestamp": timestamp,
                "level": level_upper,
                "service": service_upper,
                "message": message
            }
            if data:
                log_entry["data"] = data
            self._write_to_file(log_entry)

        # 2. Console printing
        should_print = (_vars.DEBUG and is_service_enabled) or level_upper in ["ERROR", "WARNING"]

        if should_print:
            color = ""
            reset = "\033[0m"
            if level_upper == "ERROR":
                color = "\033[91m"  # Red
            elif level_upper == "WARNING":
                color = "\033[93m"  # Yellow
            elif level_upper == "DEBUG":
                color = "\033[94m"  # Blue
            elif level_upper == "INFO":
                color = "\033[92m"  # Green
            
            prefix = f"[{service_upper}]"
            print(f"{color}{prefix:<12} [{level_upper}] {message}{reset}")
            
            if data and _vars.DEBUG:
                if "traceback" in data:
                    print(f"      {color}TRACE: {data['traceback'][-1]}{reset}")
                else:
                    # Don't print huge data blobs to console
                    pass

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
