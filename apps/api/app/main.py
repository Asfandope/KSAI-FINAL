# In apps/api/app/main.py

from pathlib import Path  # Add this import
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# --- START OF CHANGE ---
# Explicitly find and load the .env file from the same directory as this script.
# This is the most reliable way to ensure it's loaded.
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
# --- END OF CHANGE ---

from .core.config import settings
from .routers import admin, auth, chat, content

# Add logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

app = FastAPI(
    title="KS AI API",
    description="API for the KS AI bilingual chat assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("app.middleware")
    start_time = time.time()
    
    logger.info(f"🚀 {request.method} {request.url}")
    
    # Log request body for POST requests to /chat
    if request.method == "POST" and "/chat" in str(request.url):
        logger.info("📩 Chat request detected!")
        
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url} - {response.status_code} ({process_time:.3f}s)")
    
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "KS AI API"}


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(content.router, prefix="/topics", tags=["Content"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # In development, provide more detailed error info
    if settings.DEBUG:
        return JSONResponse(
            status_code=500, 
            content={"detail": f"Internal server error: {str(exc)}"}
        )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")