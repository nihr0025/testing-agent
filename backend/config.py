import os
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DB_PATH = BACKEND_DIR / "database" / "testing_platform.db"
REPORTS_DIR = BACKEND_DIR / "reports"
TEST_SCRIPTS_DIR = BACKEND_DIR / "test_scripts"
SCREENSHOTS_DIR = BACKEND_DIR / "reports" / "screenshots"

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
(TEST_SCRIPTS_DIR / "playwright").mkdir(parents=True, exist_ok=True)
(TEST_SCRIPTS_DIR / "selenium").mkdir(parents=True, exist_ok=True)
(BACKEND_DIR / "database").mkdir(parents=True, exist_ok=True)

# Helper to load .env file manually if python-dotenv isn't installed yet
def load_env_file(dotenv_path: Path):
    if not dotenv_path.exists():
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("\"'")
                if key not in os.environ or not os.environ[key]:
                    os.environ[key] = val

load_env_file(BASE_DIR / ".env")

class Config:
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Jira Settings
    JIRA_URL: str = os.getenv("JIRA_URL", "")
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL", "")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN", "")

    # MCP Jira Server
    JIRA_MCP_COMMAND: str = os.getenv("JIRA_MCP_COMMAND", "")
    JIRA_MCP_URL: str = os.getenv("JIRA_MCP_URL", "")

    # Automation Framework
    DEFAULT_AUTOMATION_FRAMEWORK: str = os.getenv("DEFAULT_AUTOMATION_FRAMEWORK", "playwright").lower()

    # Server Settings
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "5173"))

    # Security: SSRF Protection
    # By default, localhost and 127.0.0.1 are permitted for local demo / internal testing,
    # but cloud metadata endpoints (e.g. 169.254.169.254) are strictly blocked.
    BLOCKED_HOSTS: List[str] = [
        "169.254.169.254", # AWS/Azure/GCP metadata
        "metadata.google.internal",
        "instance-data"
    ]

    @classmethod
    def get_masked_key(cls, key: str) -> str:
        if not key:
            return ""
        if len(key) <= 8:
            return "****"
        return f"{key[:4]}...{key[-4:]}"

    @classmethod
    def is_openai_configured(cls) -> bool:
        return bool(cls.OPENAI_API_KEY and len(cls.OPENAI_API_KEY.strip()) > 5)

    @classmethod
    def is_jira_configured(cls) -> bool:
        return bool(cls.JIRA_URL and cls.JIRA_EMAIL and cls.JIRA_API_TOKEN)

    @classmethod
    def validate_target_url(cls, url: str) -> tuple[bool, str]:
        if not url:
            return True, ""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False, f"Invalid scheme '{parsed.scheme}'. Only http and https URLs are allowed."
            hostname = parsed.hostname or ""
            if hostname.lower() in [h.lower() for h in cls.BLOCKED_HOSTS]:
                return False, f"Access to restricted cloud metadata endpoint '{hostname}' is blocked for security."
            return True, ""
        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"

config = Config()
