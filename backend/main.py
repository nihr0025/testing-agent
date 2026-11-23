import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import config, REPORTS_DIR, SCREENSHOTS_DIR, BACKEND_DIR
from backend.database.db import init_db
from backend.routes import testing, jira, reports, settings, demo, ai_discovery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("testing_platform.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite database schema...")
    init_db()
    logger.info("Database initialized successfully.")
    logger.info(f"OpenAI configured: {config.is_openai_configured()}")
    logger.info(f"Jira configured: {config.is_jira_configured()}")
    logger.info(f"Default Automation Framework: {config.DEFAULT_AUTOMATION_FRAMEWORK.upper()}")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="AI Multi-Agent Software Testing Automation Platform",
    description="Full-stack AI QA Automation platform with 6 collaborating agents supporting Playwright and Selenium.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(testing.router)
app.include_router(jira.router)
app.include_router(reports.router)
app.include_router(settings.router)
app.include_router(demo.router)
app.include_router(ai_discovery.router)

# Mount static files for reports & screenshots
app.mount("/static/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Multi-Agent Testing Platform Backend",
        "openai_configured": config.is_openai_configured(),
        "jira_configured": config.is_jira_configured(),
        "default_framework": config.DEFAULT_AUTOMATION_FRAMEWORK
    }

# Serve frontend build if dist directory exists (mounted after all API routes)
frontend_dist = BACKEND_DIR.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=config.BACKEND_HOST, port=config.BACKEND_PORT, reload=True)
