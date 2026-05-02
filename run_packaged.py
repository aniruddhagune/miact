import uvicorn
import os
import sys

# Set environment variables for the packaged version
os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_PATH"] = "miact.db"
os.environ["DEBUG"] = "False"

from backend.main import app

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    # In packaged mode, we usually don't want reload
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
