import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = "Fgghhh00000bot"
WEBAPP_URL = "https://momodreza333.github.io/game7877/"
DB_PATH = "referrals.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = (
    "CREATE TABLE IF NOT EXISTS users ("
    "user_id INTEGER PRIMARY KEY, "
    "username TEXT, "
    "referrer_id INTEGER, "
    "invite_count INTEGER DEFAULT 0, "
    "reward_balance INTEGER DEFAULT 0)"
)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def create_user(user_id, username, referrer_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)", (user_id, username, referrer_id))
    conn.commit()
    conn.close()

def add_reward_to_referrer(referrer_id, points=1):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET invite_count = invite_count + 1, reward_balance = reward_balance + ? WHERE user_id = ?", (points, referrer_id))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    existing = get_user(user_id)

    referrer_id = None
    if context.args:
        try:
            candidate = int(context.args[0])
            if candidate != user_id:
                referrer_id = candidate
        except ValueError:
            pass

    if existing is None:
        create_user(user_id, username, referrer_id)
        if referrer_id is not None and get_user(referrer_id) is not None:
            add_reward_to_referrer(referrer_id)
            try:
                await context.bot.send_message(chat_id=referrer_id, text="یک نفر با لینک دعوت شما وارد شد!")
            except Exception as e:
                logger.warning("could not notify referrer: %s", e)

    ref_link = "https://t.me/" + BOT_USERNAME + "?start=" + str(user_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("باز کردن اپلیکیشن رفرال", web_app=WebAppInfo(url=WEBAPP_URL + "?ref=" + str(user_id)))]
    ])

    await update.message.reply_text(
        "سلام " + user.first_name + "\n\nلینک اختصاصی دعوت شما:\n" + ref_link + "\n\nبرای دیدن آمار از /myreferrals استفاده کن.",
        reply_markup=keyboard,
    )

async def myreferrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = get_user(user_id)
    if row is None:
        await update.message.reply_text("اول باید /start رو بزنی.")
        return
    _, _, _, invite_count, reward_balance = row
    ref_link = "https://t.me/" + BOT_USERNAME + "?start=" + str(user_id)
    await update.message.reply_text(
        "تعداد دعوت: " + str(invite_count) + "\nامتیاز: " + str(reward_balance) + "\n\nلینک شما:\n" + ref_link
    )

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myreferrals", myreferrals))
    logger.info("bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
