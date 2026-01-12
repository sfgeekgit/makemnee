"""
Development server launcher for MakeMNEE Bounty Board API.

Usage:
    python run.py

Environment variables (optional):
    HOST - Server host (default: 0.0.0.0)
    PORT - Server port (default: 8000)
    ENVIRONMENT - Environment mode (default: development)
"""
import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    print(f"Starting MakeMNEE Bounty Board API on {host}:{port}")
    print(f"Reload mode: {reload}")
    print(f"Docs available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )
