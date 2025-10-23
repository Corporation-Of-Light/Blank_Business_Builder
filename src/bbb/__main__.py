"""
Better Business Builder - Entry point for module execution
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    env = os.getenv("ENVIRONMENT", "development")
    reload = env == "development"

    uvicorn.run(
        "bbb.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info")
    )
