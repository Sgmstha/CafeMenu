"""
Campus Café - Web Application Entry Point
------------------------------------------
This is the main entry point for the College Café FastAPI backend server.
It handles application startup (lifespan), middleware configuration,
router registration, static asset serving, and Single Page Application (SPA) routing.

How to run:
    Option 1: python main.py (runs on 0.0.0.0:8000)
    Option 2: uvicorn main:app --reload --host 0.0.0.0
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

# Import database seeding / snapshots and sub-routers
from models.database import seed_db, cleanup_old_snapshots, save_menu_snapshot
from routers import auth, menu, orders, qr

# Instantiate the asynchronous background scheduler to handle periodic tasks (cron jobs)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Handles startup events (database seeding, starting cron jobs)
    and shutdown events (cleaning up resources).
    
    TODO: In a production app, set up and tear down a real database connection here
    (e.g., SQLAlchemy engine, PostgreSQL connection pool).
    """
    # Initialize/seed database values on startup
    seed_db()
    
    # Configure daily cron jobs:
    # 1. Save menu snapshot daily at midnight
    scheduler.add_job(save_menu_snapshot, "cron", hour=0, minute=0)
    # 2. Clean up snapshots older than 7 days daily at 12:05 AM
    scheduler.add_job(cleanup_old_snapshots, "cron", hour=0, minute=5)
    
    # Start the scheduler
    scheduler.start()
    
    yield  # The app serves requests here
    
    # Shutdown the background scheduler gracefully when the server stops
    scheduler.shutdown()


# Initialize the main FastAPI application with title, version, and lifespan events
app = FastAPI(title="College Café", version="1.0.0", lifespan=lifespan)

# Enable CORS (Cross-Origin Resource Sharing) middleware.
# Allows local developers or frontend applications to communicate with this API.
# TODO: In production, restrict allow_origins to specific domains instead of "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register sub-routers (separate API endpoints grouped by context)
app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(qr.router)

# Mount static files directory (for CSS, JS, images, etc.) if it exists
# TODO: Add cache-control headers for static files in production to optimize loading speeds
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ── Serve the single-page frontend (SPA) ───────────────────────────────────────────

FRONTEND = os.path.join(os.path.dirname(__file__), "templates", "index.html")

@app.get("/", response_class=HTMLResponse)
@app.get("/menu", response_class=HTMLResponse)
@app.get("/admin", response_class=HTMLResponse)
async def serve_spa(request: Request):
    """
    Serves the primary Single Page Application (SPA) HTML file.
    Since client-side routing is used, all major page paths (/, /menu, /admin)
    return the exact same HTML wrapper. The frontend JS handles active views.
    
    Note: Open file with UTF-8 encoding to support emojis and international characters.
    """
    with open(FRONTEND, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


if __name__ == "__main__":
    import uvicorn
    # Start the development server. 
    # Binds to 0.0.0.0 (all interfaces) to allow network scanning/connections on port 8000.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
