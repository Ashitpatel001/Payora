import logging
import sys
from pythonjsonlogger import jsonlogger


def _setup_logging():
    """Configure structured JSON logging for the entire application.
    
    Called once at import time. Every logger in the process inherits
    the JSON formatter, so individual modules must NOT call
    logging.basicConfig() themselves.
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    
    # Clear any handlers that were already attached (e.g. by pytest)
    root.handlers.clear()
    
    handler = logging.StreamHandler(sys.stderr)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    
    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


_setup_logging()
logger = logging.getLogger(__name__)
import os
from dotenv import load_dotenv

# Load root .env before any modules are initialized
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logger.info("Startup check - GROQ_API_KEY loaded: %s", bool(os.environ.get("GROQ_API_KEY")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.models.database import engine, Base
from backend.app.api import events, webhooks, cases, guardrails, batch

app = FastAPI(title="Razorpay Revenue Recovery Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

API_KEY = os.environ.get("API_KEY", "dev-secret-key")

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
        
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/health") and not request.url.path.startswith("/api/webhooks/"):
        api_key_header = request.headers.get("x-api-key")
        if api_key_header != API_KEY:
            return JSONResponse(status_code=403, content={"detail": "Invalid or missing API Key"})
    return await call_next(request)

@app.on_event("startup")
def on_startup():
    # Base.metadata.create_all(bind=engine)
    logger.info("Application starting up... using Alembic for migrations.")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

app.include_router(events.router)
app.include_router(webhooks.router)
app.include_router(cases.router)
app.include_router(guardrails.router)
app.include_router(batch.router)
