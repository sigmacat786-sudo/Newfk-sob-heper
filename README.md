# Sobi Link Helper Bot

A Telegram bot that takes raw PW/CloudFront-style video URLs, edits them into
playable manifest links, wraps them into an onrender.com playable link, and
lets you collect multiple `Title:URL` pairs into a downloadable `.txt` file.

## Repository Structure

```
SobiHelper/
├── main.py             # Pyrogram bot: commands, flow, Flask keep-alive server
├── config.py            # All secrets/config read from environment variables
├── url_editor.py         # URL pattern matching + edit rules + render URL builder
├── database.py           # MongoDB-backed per-user session state
├── requirements.txt      # Python dependencies
├── Dockerfile            # Python 3.12.1 image, exposes port 8000
├── render.yaml            # Render.com blueprint (optional, for one-click deploy)
├── .env.example            # Sample environment variables
├── .gitignore
└── README.md
```

## Environment Variables

Set these in Render's dashboard (or a local `.env` if you use something like
`python-dotenv`):

| Variable | Description |
|---|---|
| `API_ID` | Telegram API ID from my.telegram.org |
| `API_HASH` | Telegram API hash from my.telegram.org |
| `BOT_TOKEN` | Bot token from @BotFather |
| `MONGO_URL` | MongoDB connection string |
| `MONGO_DB_NAME` | Mongo database name (default `sobi_link_helper`) |
| `RENDER_PLAYER_BASE` | Base URL for the playable link generator |
| `BOT_OWNER_USERNAME` | Shown in bot messages |
| `PORT` | Web port for Render (defaults to 8000) |

## Commands

- `/start` — welcome message
- `/help` — step-by-step usage guide with a "Let's Start" button
- `/sobi` — starts the main link → title → (add more / create file) flow
- `/clear` — wipes all saved links/titles for that user

## URL Edit Rules

The bot recognizes 6 URL shapes (all normalized to a `master.m3u8` manifest
before being wrapped into the final onrender.com link):

1. `.../master.mpd?...` → `.../master.m3u8?...`
2. `.../dash/audio/X.mp4?...` → `.../master.m3u8?...`
3. Same as (1), cloudfront/testwave hosts, longer signed URLs
4. Same as (2), cloudfront/testwave hosts, longer signed URLs
5. `https://proxy.pwthor.live/play/...master.mpd?...` → strip proxy prefix to
   `https://...`, then apply rule (1)
6. `https://proxy.pwthor.live/play/...dash/audio/X.mp4?...` → strip proxy
   prefix to `https://...`, then apply rule (2)

## Deploying on Render.com

1. Push this repo to GitHub.
2. Create a new **Web Service** on Render, connect the repo.
3. Environment: Docker (Dockerfile is auto-detected).
4. Add the environment variables listed above.
5. Deploy — Render will detect the open port 8000 via the Flask keep-alive
   server bundled in `main.py`.

## Local Run

```bash
pip install -r requirements.txt
export API_ID=... API_HASH=... BOT_TOKEN=... MONGO_URL=...
python main.py
```
