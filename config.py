import os

# -------------------------
# Helper to read env vars
# -------------------------
def _env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    val = os.getenv(key, default)
    if required and (val is None or val.strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val


# -------------------------
# Telegram credentials (required)
# -------------------------
API_ID = int(_env("API_ID", required=True))
API_HASH = _env("API_HASH", required=True)
BOT_TOKEN = _env("BOT_TOKEN", required=True)
MONGO_URL = _env("MONGO_URL", required=True)
PING_URL = _env("PING_URL", "https://your-render-url.onrender.com")
# -------------------- CONFIG -------------------- #
FORCE_CHANNEL = -1003806743202
