from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from .models.database import create_tables
from .api.routes import get_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Strategic Decision Engine API",
    description="AI-powered strategic planning platform for CEOs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(get_router())

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc) if os.getenv("DEBUG", "False").lower() == "true" else "Internal server error"
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    print("🚀 Starting Strategic Decision Engine API...")
    
    # Create database tables
    create_tables()
    print("✅ Database tables initialized")
    
    print("✅ Strategic Decision Engine API is ready!")
    print(f"📚 API Documentation: http://localhost:8000/docs")
    print(f"🔍 ReDoc Documentation: http://localhost:8000/redoc")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Strategic Decision Engine API...")


if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🌟 Strategic Decision Engine API")
    print(f"🔗 Starting server at http://{host}:{port}")
    print(f"📖 API Docs will be available at http://{host}:{port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )