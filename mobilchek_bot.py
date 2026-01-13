import logging
import os
import re
import sqlite3
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.error import TelegramError

# ================== CONFIG ==================
TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_USERNAME = "@mobilcheek"
CHANNEL_ID = "@mobilcheek"
ADMIN_ID = 717893804  # O'zingizning ID raqamingiz
INSTAGRAM = "mobilcheek"
PHONE_NUMBER = "+998 77 047 47 41"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, username TEXT, phone_model TEXT,
                  user_phone TEXT, location TEXT, order_date TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS sell_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, username TEXT, model TEXT,
                  memory TEXT, color TEXT, condition TEXT,
                  box TEXT, location TEXT, phone TEXT,
                  price TEXT, request_date TEXT)''')
    conn.commit()
    conn.close()


init_db()

# ================== STATES ==================
BUY_PHONE_NUMBER, BUY_LOCATION, BUY_CONFIRM = range(3)
(SELL_MODEL, SELL_MEMORY, SELL_COLOR, SELL_CONDITION,
 SELL_BOX, SELL_LOCATION, SELL_PHONE, SELL_PRICE, SELL_CONFIRM) = range(3, 12)

# ================== PHONES DATA ==================
PHONES = {
    "poco_f3": {"name": "Poco F3", "memory": "128GB", "color": "Black", "battery": "N/A", "box": "✅ Bor",
                "condition": "⭐️ Ideal", "price": "155$"},
    "huawei_nova": {"name": "Huawei Nova 10 SE", "memory": "128GB", "color": "Gold", "battery": "N/A", "box": "✅ Bor",
                    "condition": "⭐️ Ideal", "price": "150$"},
    "iphone_13": {"name": "iPhone 13 Pro", "memory": "128GB", "color": "Black", "battery": "74%", "box": "✅ Bor",
                  "condition": "⭐️ Ideal", "price": "449$"},
    "redmi_note12": {"name": "Redmi Note 12", "memory": "128GB", "color": "Black", "battery": "N/A", "box": "✅ Bor",
                     "condition": "⭐️ Ideal", "price": "105$"}
}

# ================== LANG & HELPERS ==================
LANGUAGES = {
    "uz": {
        "welcome": "👋 <b>Assalomu alaykum!</b>\n\n🌐 Tilni tanlang:",
        "main_menu": "📋 <b>Bosh menyu</b>",
        "buy_phone": "🛒 Telefonlar",
        "sell_phone": "💰 Telefon sotish",
        "contact_admin": "👨‍💼 Admin",
        "order_success": "✅ <b>Buyurtma qabul qilindi!</b> Admin siz bilan bog'lanadi.",
        "sell_success": "✅ <b>Sotuv so'rovi yuborildi!</b>",
        "order_confirm": "❓ Ma'lumotlar to'g'rimi?\n\n📱 Model: {phone}\n📞 Tel: {user_phone}\n📍 Joy: {location}",
        "sell_confirm": "❓ Tasdiqlaysizmi?\n\n📱 {model}\n💾 {memory}\n🎨 {color}\n⭐️ {condition}\n📦 {box}\n📍 {location}\n📞 {phone}\n💵 {price}"
    }
}


def t(lang, key): return LANGUAGES.get(lang, LANGUAGES["uz"]).get(key, key)


async def check_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ================== HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")]]
    await update.message.reply_text(t("uz", "welcome"), reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()
    lang = context.user_data.get("lang", "uz")
    kb = [[InlineKeyboardButton(t(lang, "buy_phone"), callback_data="buy_list")],
          [InlineKeyboardButton(t(lang, "sell_phone"), callback_data="sell_start")],
          [InlineKeyboardButton(t(lang, "contact_admin"), callback_data="admin_info")]]

    text = t(lang, "main_menu")
    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


# --- BUY LOGIC ---
async def buy_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [[InlineKeyboardButton(f"{v['name']} - {v['price']}", callback_data=f"buy_id_{k}")] for k, v in PHONES.items()]
    await query.edit_message_text("📱 Telefonni tanlang:", reply_markup=InlineKeyboardMarkup(kb))


async def buy_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    phone_id = query.data.replace("buy_id_", "")
    context.user_data["selected_phone"] = phone_id
    p = PHONES[phone_id]
    text = f"📱 {p['name']}\n💰 Narxi: {p['price']}\n📦 Karobka: {p['box']}\n\nSotib olish uchun raqamingizni yuboring:"
    await query.edit_message_text(text)
    return BUY_PHONE_NUMBER


async def get_buy_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["user_phone"] = update.message.text
    await update.message.reply_text("📍 Turgan joyingizni yuboring:")
    return BUY_LOCATION


async def get_buy_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["user_loc"] = update.message.text
    p_name = PHONES[context.user_data["selected_phone"]]["name"]
    text = t("uz", "order_confirm").format(phone=p_name, user_phone=context.user_data["user_phone"],
                                           location=update.message.text)
    kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data="buy_confirm"),
           InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return BUY_CONFIRM


async def buy_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "buy_confirm":
        # Save to DB
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO orders (user_id, username, phone_model, user_phone, location, order_date) VALUES (?,?,?,?,?,?)",
            (query.from_user.id, query.from_user.username, context.user_data["selected_phone"],
             context.user_data["user_phone"], context.user_data["user_loc"], datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # Notify Admin
        await context.bot.send_message(ADMIN_ID,
                                       f"🆕 YANGI BUYURTMA!\n\n👤 @{query.from_user.username}\n📱 {context.user_data['selected_phone']}\n📞 {context.user_data['user_phone']}")
        await query.edit_message_text(t("uz", "order_success"))
    else:
        await query.edit_message_text("❌ Bekor qilindi.")
    return ConversationHandler.END


# --- SELL LOGIC ---
async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📱 Sotmoqchi bo'lgan telefon modelingizni yozing:")
    return SELL_MODEL


async def sell_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_model"] = update.message.text
    await update.message.reply_text("💾 Xotirasi qancha? (masalan: 128GB):")
    return SELL_MEMORY


async def sell_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_mem"] = update.message.text
    await update.message.reply_text("🎨 Rangi qanaqa?")
    return SELL_COLOR


async def sell_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_color"] = update.message.text
    await update.message.reply_text("⭐️ Holati qanday?")
    return SELL_CONDITION


async def sell_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_cond"] = update.message.text
    await update.message.reply_text("📦 Karobka-hujjat bormi?")
    return SELL_BOX

async def sell_box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_box"] = update.message.text
    await update.message.reply_text("📍 Qayerdasiz?")
    return SELL_LOCATION

async def sell_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_loc"] = update.message.text
    await update.message.reply_text("📞 Telefon raqamingiz:")
    return SELL_PHONE

async def sell_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_phone"] = update.message.text
    await update.message.reply_text("💵 Qancha so'rayapsiz?")
    return SELL_PRICE

async def sell_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_price"] = update.message.text
    d = context.user_data
    text = t("uz", "sell_confirm").format(model=d["s_model"], memory=d["s_mem"], color=d["s_color"], condition=d["s_cond"], box=d["s_box"], location=d["s_loc"], phone=d["s_phone"], price=d["s_price"])
    kb = [[InlineKeyboardButton("✅ Tasdiqlash", callback_data="sell_confirm"), InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    return SELL_CONFIRM

async def sell_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "sell_confirm":
        # Notify Admin
        await context.bot.send_message(ADMIN_ID, f"💰 SOTILADIGAN TEL!\n\n📱 {context.user_data['s_model']}\n💵 {context.user_data['s_price']}\n📞 {context.user_data['s_phone']}")
        await query.edit_message_text(t("uz", "sell_success"))
    else:
        await query.edit_message_text("❌ Bekor qilindi.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Amal bekor qilindi.",
        reply_markup=ReplyKeyboardRemove() # Shuni tekshiring
    )
    return ConversationHandler.END

# ================== MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_list, pattern="^buy_list$"),
                      CallbackQueryHandler(sell_start, pattern="^sell_start$"),
                      CallbackQueryHandler(buy_detail, pattern="^buy_id_")],
        states={
            BUY_PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_buy_phone)],
            BUY_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_buy_location)],
            BUY_CONFIRM: [CallbackQueryHandler(buy_final)],
            SELL_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_model)],
            SELL_MEMORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_memory)],
            SELL_COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_color)],
            SELL_CONDITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_condition)],
            SELL_BOX: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_box)],
            SELL_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_location)],
            SELL_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_phone)],
            SELL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_price)],
            SELL_CONFIRM: [CallbackQueryHandler(sell_final)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^lang_"))
    app.add_handler(conv_handler)

    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
