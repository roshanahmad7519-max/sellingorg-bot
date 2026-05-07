import sqlite3, time
from telegram import *
from telegram.ext import *

TOKEN = "8284255208:AAGrQQfgLzXSgrwD8zsbEuLFdlrq94_OMNk"
OWNER_ID = 6999434430

conn = sqlite3.connect("shared.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS videos (file_id TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry INTEGER)")
conn.commit()

upload_mode = {}

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    cur.execute("SELECT expiry FROM users WHERE user_id=?", (uid,))
    d = cur.fetchone()

    if not d:
    kb = [[
        InlineKeyboardButton(
            "🛒 Go To Selling Bot",
            url="t.me/no1sellerbot"
        )
    ]]

    await update.message.reply_text(
        "❌ Pehle Premium Buy Karo Fir Videos Access Milega.",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return

    if int(time.time()) > d[0]:
        await update.message.reply_text("⛔ Expired")
        return

    cur.execute("SELECT file_id FROM videos")
    vids = cur.fetchall()

    for v in vids:
        await context.bot.send_video(
            chat_id=uid,
            video=v[0],
            protect_content=True
        )

# ===== ENABLE UPLOAD =====
async def set_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    upload_mode[update.message.from_user.id] = True
    await update.message.reply_text("📤 Ab videos bhejo (one by one ya multiple)")

# ===== SAVE VIDEOS =====
async def save_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    if uid != OWNER_ID:
        return

    if not upload_mode.get(uid):
        return

    file_id = update.message.video.file_id

    cur.execute("INSERT INTO videos VALUES (?)", (file_id,))
    conn.commit()

    await update.message.reply_text("✅ Video saved")

# ===== STOP UPLOAD =====
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    upload_mode[update.message.from_user.id] = False
    await update.message.reply_text("✅ Upload complete")

# ===== CLEAR ALL VIDEOS =====
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    cur.execute("DELETE FROM videos")
    conn.commit()

    await update.message.reply_text("🗑 All videos deleted")

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", set_videos))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(MessageHandler(filters.VIDEO, save_video))

app.run_polling()