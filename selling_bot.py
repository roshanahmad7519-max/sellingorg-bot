OWNER_USERNAME = "OWNEROFBOTS"

import sqlite3, qrcode, time, urllib.parse
from telegram import *
from telegram.ext import *

TOKEN = "PASTE_YOUR_BOT_TOKEN"
OWNER_ID = 6999434430

PRIVATE_BOT_LINK = "https://t.me/highqualityvideobot"
DEMO_BOT_LINK = "https://t.me/demovideogiverbot"

conn = sqlite3.connect("shared.db", check_same_thread=False)
cur = conn.cursor()

# ===== TABLES =====
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT, price INTEGER, expiry_days INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

# ===== DEFAULT SETTINGS =====
cur.execute("INSERT OR IGNORE INTO settings VALUES ('upi','yourupi@upi')")
cur.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_text','🔥 Welcome! Choose Product 👇')")
cur.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_photo','')")
conn.commit()

user_selected = {}
user_state = {}

def get_setting(key):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    return cur.fetchone()[0]

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cur.execute("SELECT * FROM products")
    data = cur.fetchall()

    keyboard = [
        [InlineKeyboardButton(p[1], callback_data=p[0])]
        for p in data
    ]

    keyboard.append([
        InlineKeyboardButton(
            "🎬 Demo",
            url=DEMO_BOT_LINK
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "📞 Contact Customer Support",
            url=f"https://t.me/{OWNER_USERNAME}"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "💬 Contact On WhatsApp",
            url="https://wa.me/48699524127"
        )
    ])

    text = get_setting("welcome_text")
    photo = get_setting("welcome_photo")

    if photo:
        await update.message.reply_photo(
            photo=photo,
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ===== PRODUCT =====
async def product_click(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    pid = q.data

    cur.execute("SELECT * FROM products WHERE id=?", (pid,))
    p = cur.fetchone()

    if not p:
        return

    amount = p[2]
    upi = get_setting("upi")

    note = urllib.parse.quote(p[1])

    upi_link = f"upi://pay?pa={upi}&pn=Shop&am={amount}&cu=INR&tn={note}"

    img = qrcode.make(upi_link)

    file = f"{pid}.png"
    img.save(file)

    user_selected[q.from_user.id] = pid

    await q.message.reply_photo(
        photo=open(file, "rb"),
        caption=f"💰 Pay ₹{amount}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Verify", callback_data="verify")]
        ])
    )

# ===== STATS =====
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != OWNER_ID:
        return

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE expiry > ?",
        (int(time.time()),)
    )

    active_users = cur.fetchone()[0]

    text = f"""
📊 BOT STATS

👥 Total Users: {total_users}
✅ Active Buyers: {active_users}
"""

    await update.message.reply_text(text)

# ===== VERIFY =====
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    await q.message.reply_text("📸 Screenshot bhejo")

# ===== SCREENSHOT =====
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user

    pid = user_selected.get(user.id)

    if not pid:
        return

    cur.execute("SELECT * FROM products WHERE id=?", (pid,))
    p = cur.fetchone()

    if not p:
        return

    kb = [
        [
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve_{user.id}"
            ),

            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject_{user.id}"
            )
        ],

        [
            InlineKeyboardButton(
                "💬 Chat",
                url=f"tg://user?id={user.id}"
            )
        ]
    ]

    await context.bot.send_photo(
        chat_id=OWNER_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"{user.id} | {p[1]} | ₹{p[2]} | {p[3]}d",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ===== REJECT =====
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    kb = [[
        InlineKeyboardButton(
            "📞 Customer Support",
            url=f"https://t.me/{OWNEROFBOTS}"
        )
    ]]

    await context.bot.send_message(
        chat_id=uid,
        text="""
❌ AREY SIR AAP PLEASE PEHLE PAYMENT KERO FIR REAL SCREENSHOT BEJHO.

AAPNE YAA TOH FAKE SCREENSHOT BEJHA HAI YA AAPNE PAYMENT NAHI KIYA HAI.

ISS LIYE HAM AAPKO PAID VIDEOS KA ACCESS NAHI DEH SAKTE HAI SORRY.

AGAR AAPKO KOI DOUBT HAI TOH CUSTOMER SUPPORT BUTTON PEH CLICK KERO AUR MUJHE MESSAGE KERO.
""",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    await q.message.reply_text("❌ Rejected")

# ===== APPROVE =====
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    pid = user_selected.get(uid)

    cur.execute("SELECT * FROM products WHERE id=?", (pid,))
    p = cur.fetchone()

    if not p:
        return

    expiry = int(time.time()) + p[3] * 86400

    cur.execute(
        "INSERT OR REPLACE INTO users VALUES (?,?)",
        (uid, expiry)
    )

    conn.commit()

    await context.bot.send_message(
        uid,
        f"✅ Approved\n\n🔐 {https://t.me/highqualityvideobot}"
    )

    await q.message.reply_text("✅ Approved Successfully")

# ===== ADMIN =====
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != OWNER_ID:
        return

    kb = [
        [InlineKeyboardButton("➕ Add Product", callback_data="add")],
        [InlineKeyboardButton("💳 Change UPI", callback_data="upi")],
        [InlineKeyboardButton("✏️ Welcome Text", callback_data="text")],
        [InlineKeyboardButton("🖼 Welcome Photo", callback_data="photo")]
    ]

    await update.message.reply_text(
        "Admin Panel",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ===== BUTTON =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user_state[q.from_user.id] = q.data

    await q.message.reply_text("Send data")

# ===== TEXT =====
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != OWNER_ID:
        return

    state = user_state.get(update.message.from_user.id)

    if state == "add":

        pid, name, price, exp = update.message.text.split()

        cur.execute(
            "INSERT INTO products VALUES (?,?,?,?)",
            (pid, name, int(price), int(exp))
        )

        conn.commit()

        await update.message.reply_text("✅ Product Added")

    elif state == "upi":

        cur.execute(
            "INSERT OR REPLACE INTO settings VALUES ('upi',?)",
            (update.message.text,)
        )

        conn.commit()

        await update.message.reply_text("✅ UPI Updated")

    elif state == "text":

        cur.execute(
            "INSERT OR REPLACE INTO settings VALUES ('welcome_text',?)",
            (update.message.text,)
        )

        conn.commit()

        await update.message.reply_text("✅ Text Updated")

# ===== PHOTO =====
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if user_state.get(update.message.from_user.id) == "photo":

        fid = update.message.photo[-1].file_id

        cur.execute(
            "INSERT OR REPLACE INTO settings VALUES ('welcome_photo',?)",
            (fid,)
        )

        conn.commit()

        await update.message.reply_text("✅ Photo Updated")

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(approve, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="reject_"))
app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
app.add_handler(CallbackQueryHandler(buttons, pattern="add|upi|text|photo"))
app.add_handler(CallbackQueryHandler(product_click))

app.add_handler(MessageHandler(filters.PHOTO, screenshot))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
app.add_handler(MessageHandler(filters.PHOTO, photo))

app.run_polling()