"""
database.py
─────────────────────────────────────────────────────────────────────────────
MongoDB-backed storage for per-user session state:
  - list of {title, url} entries collected so far
  - current step in the flow ("await_url", "await_title", "await_filename", None)
  - temp holder for the last edited URL while waiting for its title
"""

from pymongo import MongoClient
from config import MONGO_URL, MONGO_DB_NAME

_client = MongoClient(MONGO_URL)
_db = _client[MONGO_DB_NAME]
sessions = _db["sessions"]


def get_session(user_id: int) -> dict:
    doc = sessions.find_one({"_id": user_id})
    if not doc:
        doc = {
            "_id": user_id,
            "entries": [],       # list of {"title": str, "url": str, "image_url": str|None}
            "step": None,        # None | "await_url" | "await_title" | "await_image" | "await_filename"
            "pending_url": None,  # holds the edited final url while waiting for its title
            "pending_title": None,  # holds the title while waiting for its image url
        }
        sessions.insert_one(doc)
    return doc


def set_step(user_id: int, step: str | None):
    sessions.update_one({"_id": user_id}, {"$set": {"step": step}}, upsert=True)


def set_pending_url(user_id: int, url: str | None):
    sessions.update_one({"_id": user_id}, {"$set": {"pending_url": url}}, upsert=True)


def set_pending_title(user_id: int, title: str | None):
    sessions.update_one({"_id": user_id}, {"$set": {"pending_title": title}}, upsert=True)


def add_entry(user_id: int, title: str, url: str, image_url: str | None = None):
    sessions.update_one(
        {"_id": user_id},
        {"$push": {"entries": {"title": title, "url": url, "image_url": image_url}}},
        upsert=True,
    )


def get_entries(user_id: int) -> list:
    doc = get_session(user_id)
    return doc.get("entries", [])


def clear_session(user_id: int):
    sessions.update_one(
        {"_id": user_id},
        {"$set": {"entries": [], "step": None, "pending_url": None, "pending_title": None}},
        upsert=True,
    )
