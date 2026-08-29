import os
from dotenv import load_dotenv

# Load root .env before any modules are initialized
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

print("Startup check - GROQ_API_KEY loaded:", bool(os.environ.get("GROQ_API_KEY")))

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

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

app.include_router(events.router)
app.include_router(webhooks.router)
app.include_router(cases.router)
app.include_router(guardrails.router)
app.include_router(batch.router)
