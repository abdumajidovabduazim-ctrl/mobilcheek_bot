import logging
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
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
ADMIN_ID = 717893804
INSTAGRAM = "mobilcheek"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ================== STATES ==================
(
    SELL_MODEL,
    SELL_MEMORY,
    SELL_COLOR,
    SELL_CONDITION,
    SELL_BOX,
    SELL_LOCATION,
    SELL_PHONE,
    SELL_PRICE,
) = range(8)

# ================== LANG ==================
LANGUAGES = {
    "uz": {
        "welcome": "👋 Assalomu alaykum!\n\nTilni tanlang:",
        "choose_lang": "🌐 Tilni tanlang:",
        "subscription_required": "📢 Avval kanalga obuna bo‘ling:\n{channel}",
        "subscribe_btn": "✅ Obuna bo‘lish",
        "check_sub_btn": "🔄 Tekshirish",
        "subscribed": "✅ Obuna tasdiqlandi!",
        "not_subscribed": "❌ Hali obuna emassiz!",
        "main_menu": "📋 <b>Bosh menyu</b>",
        "buy_phone": "🛒 Telefonlar",
        "sell_phone": "💰 Telefon sotish",
        "contact_admin": "💬 Admin",
        "info": "ℹ️ Ma'lumot",
        "back": "🔙 Orqaga",
        "main_menu_btn": "🏠 Bosh menyu",
        "phones_list": "📱 Telefonlar:",
        "order_btn": "✅ Buyurtma",
        "order_success": "✅ Buyurtma qabul qilindi!",
        "order_error": "❌ Xatolik!",
        "sell_start": "📱 Telefon modelini yozing:",
        "sell_memory_q": "💾 Xotira?",
        "sell_color_q": "🎨 Rang?",
        "sell_condition_q": "⭐ Holat?",
        "sell_box_q": "📦 Karobka?",
        "sell_location_q": "📍 Joylashuv?",
        "sell_phone_q": "📞 Telefon raqam?",
        "sell_price_q": "💵 Narx?",
        "sell_success": "✅ Ma'lumot yuborildi!",
        "cancel": "❌ Bekor qilindi",
        "ideal": "⭐ Ideal",
        "good": "👍 Yaxshi",
        "bad": "👌 Qoniqarli",
        "box_yes": "📦 Bor",
        "box_no": "❌ Yo‘q",
    }
}

def t(lang, key):
    return LANGUAGES[lang][key]

# ================== HELPERS ==================
async def check_sub(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError:
        return False

def lang_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O‘zbek", callback_data="lang_uz")]
    ])

def main_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "buy_phone"), callback_data="buy_phone")],
        [InlineKeyboardButton(t(lang, "sell_phone"), callback_data="sell_phone")],
        [InlineKeyboardButton(t(lang, "contact_admin"), callback_data="contact_admin")],
    ])

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("uz", "welcome"), reply_markup=lang_kb())

async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_")[1]
    context.user_data["lang"] = lang

    if not await check_sub(q.from_user.id, context):
        await q.edit_message_text(
            t(lang, "subscription_required").format(channel=CHANNEL_USERNAME),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(lang, "subscribe_btn"), url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                [InlineKeyboardButton(t(lang, "check_sub_btn"), callback_data="check_sub")]
            ])
        )
        return

    await q.edit_message_text(t(lang, "main_menu"), reply_markup=main_menu(lang), parse_mode="HTML")

async def check_sub_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "uz")

    if await check_sub(q.from_user.id, context):
        await q.edit_message_text(t(lang, "main_menu"), reply_markup=main_menu(lang), parse_mode="HTML")
    else:
        await q.answer(t(lang, "not_subscribed"), show_alert=True)

# ================== BUY ==================
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "uz")

    await q.edit_message_text(
        "📱 iPhone 15 — 475$\n📱 Xiaomi 11T — 189$",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(lang, "main_menu_btn"), callback_data="back")]
        ])
    )

# ================== SELL CONVERSATION ==================
async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "uz")
    await q.edit_message_text(t(lang, "sell_start"))
    return SELL_MODEL

async def sell_model(update, context):
    context.user_data["model"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "sell_memory_q"))
    return SELL_MEMORY

async def sell_memory(update, context):
    context.user_data["memory"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "sell_color_q"))
    return SELL_COLOR

async def sell_color(update, context):
    context.user_data["color"] = update.message.text
    lang = context.user_data["lang"]
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(t(lang, "ideal")), KeyboardButton(t(lang, "good"))]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(t(lang, "sell_condition_q"), reply_markup=kb)
    return SELL_CONDITION

async def sell_condition(update, context):
    context.user_data["condition"] = update.message.text
    lang = context.user_data["lang"]
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton(t(lang, "box_yes")), KeyboardButton(t(lang, "box_no"))]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(t(lang, "sell_box_q"), reply_markup=kb)
    return SELL_BOX

async def sell_box(update, context):
    context.user_data["box"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "sell_location_q"))
    return SELL_LOCATION

async def sell_location(update, context):
    context.user_data["location"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "sell_phone_q"))
    return SELL_PHONE

async def sell_phone(update, context):
    context.user_data["phone"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "sell_price_q"))
    return SELL_PRICE

async def sell_price(update, context):
    context.user_data["price"] = update.message.text
    lang = context.user_data["lang"]

    msg = "\n".join([f"{k}: {v}" for k, v in context.user_data.items()])
    await context.bot.send_message(ADMIN_ID, msg)
    await update.message.reply_text(t(lang, "sell_success"))
    return ConversationHandler.END

# ================== OTHER ==================
async def back(update, context):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "uz")
    await q.edit_message_text(t(lang, "main_menu"), reply_markup=main_menu(lang), parse_mode="HTML")

# ================== MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_lang, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(check_sub_cb, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_phone$"))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))

    sell_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(sell_start, pattern="^sell_phone$")],
        states={
            SELL_MODEL: [MessageHandler(filters.TEXT, sell_model)],
            SELL_MEMORY: [MessageHandler(filters.TEXT, sell_memory)],
            SELL_COLOR: [MessageHandler(filters.TEXT, sell_color)],
            SELL_CONDITION: [MessageHandler(filters.TEXT, sell_condition)],
            SELL_BOX: [MessageHandler(filters.TEXT, sell_box)],
            SELL_LOCATION: [MessageHandler(filters.TEXT, sell_location)],
            SELL_PHONE: [MessageHandler(filters.TEXT, sell_phone)],
            SELL_PRICE: [MessageHandler(filters.TEXT, sell_price)],
        },
        fallbacks=[],
    )

    app.add_handler(sell_conv)

    app.run_polling()

if __name__ == "__main__":
    main()
