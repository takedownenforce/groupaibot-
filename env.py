import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# -------------------- Environment Variables -------------------- #
API_ID = os.getenv("API_ID", "").strip()
API_HASH = os.getenv("API_HASH", "").strip()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# -------------------- Validation -------------------- #
if not API_ID:
    raise SystemExit("❌ API_ID not found. Exiting...")
elif not API_HASH:
    raise SystemExit("❌ API_HASH not found. Exiting...")
elif not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN not found. Exiting...")
# -------------------- Type Correction -------------------- #
try:
    API_ID = int(API_ID)
except ValueError:
    raise SystemExit("❌ API_ID must be an integer. Exiting...")

# -------------------- Database Fixes -------------------- #
# Fix DATABASE_URL if using PostgreSQL (Heroku / VPS)
