"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import os

from app.models.database import create_tables
from app.api import auth, settings, bot

app = FastAPI(
    title="F&O Sentinel",
    description="F&O Trading Bot Web Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
static_path = os.path.join(frontend_path, "static")
templates_path = os.path.join(frontend_path, "templates")

app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)

# API Routes
app.include_router(auth.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(bot.router, prefix="/api")

from fastapi.responses import RedirectResponse
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url="/static/img/fo_sentinel_favicon.png")

# DB init on startup
@app.on_event("startup")
async def startup():
    create_tables()


# Serve the SPA for all non-API routes
@app.get("/")
@app.get("/app")
async def serve_app(request: Request):
    return templates.TemplateResponse("app.html", {"request": request})


@app.get("/login")
async def serve_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register")
async def serve_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/forgot-password")
async def serve_forgot_password(request: Request):
    return templates.TemplateResponse("forgot-password.html", {"request": request})


@app.get("/reset-password")
async def serve_reset_password(request: Request):
    return templates.TemplateResponse("reset-password.html", {"request": request})
