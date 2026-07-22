import os

# ─── Telegram Bot Config ───────────────────────────────────────────────────
API_ID = int(os.environ.get("API_ID", "22518279"))
API_HASH = os.environ.get("API_HASH", "61e5cc94bc5e6318643707054e54caf4")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ─── MongoDB Config ─────────────────────────────────────────────────────────
MONGO_URL = os.environ.get(
    "MONGO_URL",
    "mongodb+srv://devms786178_db_user:cEtMdLjmHF5EM2Pf@cluster0.xbqyvnn.mongodb.net/?appName=Cluster0"
)
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "sobi_link_helper")

# ─── Render / Web Server Config ────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 8000))

# ─── Render Playable URL Base ──────────────────────────────────────────────
# This is the base used to build the final onrender.com playable link.
# Final link => RENDER_PLAYER_BASE + urlencode(edited_video_url)
RENDER_PLAYER_BASE = os.environ.get(
    "RENDER_PLAYER_BASE",
    "https://learnwithpw-recorded.onrender.com/play?v="
)

# ─── Bot Identity ───────────────────────────────────────────────────────────
BOT_OWNER_USERNAME = os.environ.get("BOT_OWNER_USERNAME", "@SmartBoy_ApnaMS")
