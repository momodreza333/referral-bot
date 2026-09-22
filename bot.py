import os
import sqlite3
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# ---------- تنظیمات ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")
BOT_USERNAME = "Fgghhh00000bot"
WEBAPP_URL = "https://momodreza333.github.io/"
DB_PATH = "referrals.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- دیتابیس ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "user_id INTEGER PRIMARY KEY, "
        "username TEXT, "
        "referred_by INTEGER, "
        "referral_count INTEGER DEFAULT 0"
        ")"
    )
    conn.commit()
    conn.close()

def add_user(user_id, username, referred_by=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    exists = cur.fetchone()
    if not exists:
        cur.execute(
            "INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
            (user_id, username, referred_by),
        )
        if referred_by:
            cur.execute(
                "UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?",
                (referred_by,),
            )
        conn.commit()
    conn.close()
    return exists is None

def get_referral_count(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT referral_count FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

# ---------- دستورات بات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referred_by = None

    if context.args:
        try:
            ref_id = int(context.args[0])
            if ref_id != user.id:
                referred_by = ref_id
        except ValueError:
            pass

    is_new = add_user(user.id, user.username or user.first_name, referred_by)

    ref_link = f"https://t.me/{BOT_USERNAME}?start={user.id}"
    count = get_referral_count(user.id)

    keyboard = [
        [InlineKeyboardButton("🚀 باز کردن اپلیکیشن", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("📊 تعداد زیرمجموعه‌ها", callback_data="stats")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"سلام {user.first_name} 👋\n\n"
        f"لینک رفرال شما:\n{ref_link}\n\n"
        f"تعداد زیرمجموعه‌های شما: {count}\n\n"
        "این لینک رو برای دوستانت بفرست تا زیرمجموعه‌ت اضافه شه، هیچ محدودیتی نداره."
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    count = get_referral_count(user.id)
    await update.message.reply_text(f"تعداد زیرمجموعه‌های شما: {count}")

# ---------- وب‌سرور کوچیک برای زنده نگه داشتن روی Render ----------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot is running."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

# ---------- اجرای اصلی ----------
def main():
    init_db()

    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))

    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
