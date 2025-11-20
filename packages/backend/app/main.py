"""FastAPI application entry point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import init_db, close_db
from app.rate_limit import limiter
from app.routers import logs, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    await init_db()
    yield
    # Shutdown
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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "AI Usage Firewall API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
