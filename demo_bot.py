OWNER_USERNAME = "OWNEROFBOTS"
import sqlite3, asyncio
from telegram import *
from telegram.ext import *

TOKEN = "8786727671:AAEQC1CKjOQPidrt_Dd497A66fGNoLjai0k"
OWNER_ID = 6999434430

conn = sqlite3.connect("shared.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS demo_videos (file_id TEXT)")
conn.commit()

upload = {}

async def start(update, context):
    cur.execute("SELECT file_id FROM demo_videos")
    for v in cur.fetchall():
        msg = await context.bot.send_video(update.message.chat_id, v[0], protect_content=True)
        asyncio.create_task(delete(context, msg.chat_id, msg.message_id))

kb = [
    [
        InlineKeyboardButton(
            "📞 Contact Customer Support",
            url="https://t.me/OWNEROFBOTS"
        )
    ],
    [
        InlineKeyboardButton(
            "🛒 Purchase The 50K Videos",
            url="t.me/no1sellerbot"
        )
    ]
]

await update.message.reply_text(
    "Need Help?",
    reply_markup=InlineKeyboardMarkup(kb)
)

async def delete(context, cid, mid):
    await asyncio.sleep(30)
    try: await context.bot.delete_message(cid, mid)
    except: pass

async def setv(update, context):
    upload[update.message.from_user.id] = True
    await update.message.reply_text("Send videos")

async def save(update, context):
    if upload.get(update.message.from_user.id):
        cur.execute("INSERT INTO demo_videos VALUES (?)", (update.message.video.file_id,))
        conn.commit()

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", setv))
app.add_handler(MessageHandler(filters.VIDEO, save))
app.run_polling()