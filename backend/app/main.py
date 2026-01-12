"""
MakeMNEE Bounty Board API - Main Application

FastAPI application for storing bounty metadata and handling agent submissions.
The smart contracts handle all payment logic; this API is just a metadata layer.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.api import bounties, submissions

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="MakeMNEE Bounty Board API",
    description="API for AI agents to discover and complete bounties",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
# Allow all origins for development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(bounties.router, prefix="/api", tags=["bounties"])
app.include_router(submissions.router, prefix="/api", tags=["submissions"])


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information.

    Returns:
        dict: API information and documentation links
    """
    return {
        "message": "MakeMNEE Bounty Board API",
        "description": "API for AI agents to discover and complete bounties",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "list_bounties": "GET /api/bounties",
            "get_bounty": "GET /api/bounty/{id}",
            "create_bounty": "POST /api/bounty",
            "submit_work": "POST /api/bounty/{id}/submit",
            "get_submissions": "GET /api/bounty/{id}/submissions"
        }
    }


# Health check endpoint
@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "makemnee-api",
        "version": "1.0.0"
    }


# Exception handlers

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    # Log the error in production
    print(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
