import os
import asyncio
import threading

from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import API_ID, API_HASH, BOT_TOKEN, PORT, BOT_OWNER_USERNAME
from url_editor import process_raw_url, looks_like_url
import database as db

# ─── Flask keep-alive server for Render ───────────────────────────────────────
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return 'Bot is running!'

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host="0.0.0.0", port=port)

# Start Flask in background thread so Render detects open port
threading.Thread(target=run_flask, daemon=True).start()
# ─────────────────────────────────────────

app = Client(
    "sobi_link_helper_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

DELETE_DELAY = 7  # seconds, for the "await delete true" messages
IMAGE_STEP_BOT_DELETE_DELAY = 10  # seconds, bot's image-url prompt/confirmation messages
IMAGE_STEP_USER_DELETE_DELAY = 5  # seconds, user's image-url input message


async def auto_delete(message: Message, delay: int = DELETE_DELAY):
    """Delete a message after `delay` seconds, ignoring any failure."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


def schedule_delete(message: Message, delay: int = DELETE_DELAY):
    asyncio.create_task(auto_delete(message, delay))


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    text = (
        "**Welcome** {mention} ❤️🤭.\n"
        "**send me Any Link!**\n"
        "i will edits and Create a txt file for you\n\n"
        "Know more about how to use me send /help to Me Hurry up😘.\n\n"
        "If you know about me so just send /Sobi to me and see my magic ✨.\n\n"
        f"**Made By**: {BOT_OWNER_USERNAME}\n\n"
        f"**Supported Websites:**\n"
        f"https://pwthor.live **And**\n"
        f"https://vidcloud.eu.org\n\n"
        f"**🔰WARNINGS🔰**\n\n"
        f"**i can use your previous Link too😥\n"
        f"**So if you use me again\n**"
        f"**So first Clear Your History By: /Clear Command!☺"
    )
    await message.reply_text(text)


# ─────────────────────────────────────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────────────────────────────────────
HELP_TEXT = (
    "**1.** Send me Any Link!\n"
    "**2.** Send the Title Message for your Video Title\n"
    "**3.** Send me the Image url(thumbnail url) for that video, or send "
    "/Skip to skip it\n"
    "**4.** If you want adding more links so tap on Add Button or tap on "
    "Create file button\n"
    "**5.** If you choose Add Button then Step 1, Step 2, Step 3 and Step 4 "
    "will be repeat (Flow continuously, no limit of your message or links)\n"
    "**6.** If you choose Create File so then i will ask to you Your txt "
    "file Name.\n"
    "**7.** After sending file name i will give you your txt file."
)

@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Let's Start🥰", callback_data="go_sobi")]]
    )
    await message.reply_text(HELP_TEXT, reply_markup=markup)


@app.on_callback_query(filters.regex("^go_sobi$"))
async def go_sobi_callback(client: Client, cq: CallbackQuery):
    await cq.answer()
    await sobi_flow_start(client, cq.message.chat.id, cq.from_user.id)


# ─────────────────────────────────────────────────────────────────────────────
# /Sobi (main flow)
# ─────────────────────────────────────────────────────────────────────────────
async def sobi_flow_start(client: Client, chat_id: int, user_id: int):
    db.set_step(user_id, "await_url")
    db.set_pending_url(user_id, None)
    db.set_pending_title(user_id, None)
    msg = await client.send_message(chat_id, "**Yahoo😻**!\n\n**Send me Your Link! 🔗**")
    schedule_delete(msg)


@app.on_message(filters.command("sobi", prefixes=["/"]) & filters.private)
async def sobi_cmd(client: Client, message: Message):
    await sobi_flow_start(client, message.chat.id, message.from_user.id)


# ─────────────────────────────────────────────────────────────────────────────
# /clear
# ─────────────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("clear") & filters.private)
async def clear_cmd(client: Client, message: Message):
    db.clear_session(message.from_user.id)
    await message.reply_text("**Perfect😁 \nI deleted Our All Conversations.**")
    schedule_delete(message)


# ─────────────────────────────────────────────────────────────────────────────
# Add More / Create File buttons
# ─────────────────────────────────────────────────────────────────────────────
async def send_progress_prompt(client: Client, chat_id: int, user_id: int):
    entries = db.get_entries(user_id)
    count = len(entries)
    text = (
        f"Great 😉\n"
        f"**I saved Your Url {count} do you wanna add more?**\n\n"
        f"Or would you likes to Create txt file Now?!"
    )
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Add More ✨", callback_data="add_more"),
                InlineKeyboardButton("Create Txt File 🗃️", callback_data="create_file"),
            ]
        ]
    )
    await client.send_message(chat_id, text, reply_markup=markup)


@app.on_callback_query(filters.regex("^add_more$"))
async def add_more_callback(client: Client, cq: CallbackQuery):
    await cq.answer()
    user_id = cq.from_user.id
    db.set_step(user_id, "await_url")
    db.set_pending_url(user_id, None)
    db.set_pending_title(user_id, None)
    entries = db.get_entries(user_id)
    next_no = len(entries) + 1
    msg = await cq.message.reply_text(f"Your {next_no}th Now send link")
    schedule_delete(msg)
    try:
        await cq.message.delete()
    except Exception:
        pass


@app.on_callback_query(filters.regex("^create_file$"))
async def create_file_callback(client: Client, cq: CallbackQuery):
    await cq.answer()
    user_id = cq.from_user.id
    db.set_step(user_id, "await_filename")
    msg = await cq.message.reply_text(
        "**Aaahaan😎\nNow Send me Txt file Name(without extension)!**"
    )
    try:
        await cq.message.delete()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Generic text handler - drives the step machine (url -> title -> ... / filename)
# ─────────────────────────────────────────────────────────────────────────────
@app.on_message(
    filters.private
    & filters.text
    & ~filters.command(["start", "help", "sobi", "clear"])
)
async def text_router(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    session = db.get_session(user_id)
    step = session.get("step")

    if step == "await_url":
        await handle_url_input(client, message)
    elif step == "await_title":
        await handle_title_input(client, message)
    elif step == "await_image":
        await handle_image_input(client, message)
    elif step == "await_filename":
        await handle_filename_input(client, message)
    # else: no active flow, ignore silently (bot only reacts inside /Sobi flow)


async def handle_url_input(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    raw_text = message.text.strip()

    if not looks_like_url(raw_text):
        warn = await message.reply_text(
            "**That doesn't look like a link. Please send a valid URL. 🔗**"
        )
        schedule_delete(warn)
        schedule_delete(message)
        return

    editing_msg = await message.reply_text("**WOW🥳\n\nim editing this URL Wait...🔍**")

    final_url = process_raw_url(raw_text)

    schedule_delete(editing_msg, delay=2)

    if final_url is None:
        err = await message.reply_text(
            "*I couldn't recognize this link format. Please send a supported link❌.\n\nForward Your Link Here:\n@SmartBoy_ApnaMS**"
        )
        schedule_delete(err)
        schedule_delete(message)
        return

    db.set_pending_url(user_id, final_url)
    db.set_step(user_id, "await_title")

    prompt = await message.reply_text("**Alright🥰\nNow Send Me Your Video Titel**.")
    schedule_delete(message)


async def handle_title_input(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    title = message.text.strip()

    session = db.get_session(user_id)
    pending_url = session.get("pending_url")

    if not pending_url:
        # Shouldn't normally happen, reset flow
        db.set_step(user_id, "await_url")
        err = await message.reply_text("**Something went wrong, send me the link again. 🔗**")
        schedule_delete(err)
        schedule_delete(message)
        return

    db.set_pending_title(user_id, title)
    db.set_step(user_id, "await_image")

    schedule_delete(message)

    prompt = await message.reply_text(
        "**NO Send image url(thumbnail url) or\n\nYou can /Skip it ! **"
    )
    schedule_delete(prompt, delay=IMAGE_STEP_BOT_DELETE_DELAY)


async def handle_image_input(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    raw_text = message.text.strip()

    session = db.get_session(user_id)
    pending_url = session.get("pending_url")
    pending_title = session.get("pending_title")

    if not pending_url or not pending_title:
        # Shouldn't normally happen, reset flow
        db.set_step(user_id, "await_url")
        err = await message.reply_text("**Something went wrong, send me the link again. 🔗**")
        schedule_delete(err)
        schedule_delete(message, delay=IMAGE_STEP_USER_DELETE_DELAY)
        return

    if raw_text.lower() == "/skip":
        image_url = None
    else:
        if not looks_like_url(raw_text):
            warn = await message.reply_text(
                "**That doesn't look like a link. Please send a valid image url or /Skip it! 🔗**"
            )
            schedule_delete(warn, delay=IMAGE_STEP_BOT_DELETE_DELAY)
            schedule_delete(message, delay=IMAGE_STEP_USER_DELETE_DELAY)
            return
        image_url = raw_text

    db.add_entry(user_id, pending_title, pending_url, image_url)
    db.set_pending_url(user_id, None)
    db.set_pending_title(user_id, None)
    db.set_step(user_id, None)

    schedule_delete(message, delay=IMAGE_STEP_USER_DELETE_DELAY)

    await send_progress_prompt(client, chat_id, user_id)


async def handle_filename_input(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    filename = message.text.strip()

    entries = db.get_entries(user_id)
    if not entries:
        err = await message.reply_text("**No links saved yet. Send /Sobi to start. ✨**")
        schedule_delete(err)
        schedule_delete(message)
        db.set_step(user_id, None)
        return

    lines = [
        f"{e['title']}:{e['url']}||{e.get('image_url') or ''}" for e in entries
    ]
    content = "\n".join(lines)

    safe_name = filename if filename else "SobiLinks"
    file_path = f"/tmp/{safe_name}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    caption = (
        f"File Name: {filename}\n"
        f"Totel Url in this File: {len(entries)}\n\n"
        f"**Wanna use me again so send me /Sobi again im Here Habibi☺️.**\n"
        f"**Bot Made By**: {BOT_OWNER_USERNAME}"
        f"**Please:** /Clear it Now!"
    )

    await client.send_document(chat_id, file_path, caption=caption)

    try:
        os.remove(file_path)
    except Exception:
        pass

    db.set_step(user_id, None)
    schedule_delete(message)


if __name__ == "__main__":
    app.run()
