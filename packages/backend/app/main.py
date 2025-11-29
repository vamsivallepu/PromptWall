"""FastAPI application entry point"""
from contextlib import asynccontextmanager
import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import init_db, close_db
from app.rate_limit import limiter
from app.routers import logs, config, admin, classify
from app.scheduler import schedule_retention_cleanup

# Global variable to hold the background task
background_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await init_db()
    
    # Start background scheduler if enabled
    enable_scheduler = os.getenv("ENABLE_RETENTION_SCHEDULER", "false").lower() == "true"
    scheduler_interval = int(os.getenv("RETENTION_CLEANUP_INTERVAL_HOURS", "24"))
    
    if enable_scheduler:
        task = asyncio.create_task(schedule_retention_cleanup(scheduler_interval))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    
    yield
    
    # Shutdown
    # Cancel background tasks
    for task in background_tasks:
        task.cancel()
    
    await close_db()


app = FastAPI(
    title="AI Usage Firewall API",
    description="Backend API for monitoring and controlling AI tool usage",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(logs.router)
app.include_router(config.router)
app.include_router(admin.router)
app.include_router(classify.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "AI Usage Firewall API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
