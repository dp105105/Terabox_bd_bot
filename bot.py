import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

# Environment Variables
BOT_TOKEN = os.environ.get("8557431228:AAFwo1XGYQ3YcCKW9EgsnpufzKPEnaONxhk")  # Render / Railway ENV
ADMIN_ID = int(os.environ.get("7407760366"))

# In-memory storage
paid_users = {}  # user_id: True
used_txn = set()

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /buy to get premium access.")

# /buy command
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Pay via bKash / Nagad / Bank\n"
        "Send your TXN ID using /pay <TXN_ID> then send screenshot."
    )

# /pay command
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 1:
        await update.message.reply_text("Send TXN ID after /pay command.")
        return
    txn_id = context.args[0]
    if txn_id in used_txn:
        await update.message.reply_text("❌ This TXN ID is already used!")
        return

    # Save txn for screenshot
    context.user_data["txn"] = txn_id
    await update.message.reply_text("✅ TXN received. Now send screenshot of payment.")

# Screenshot handler
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    txn = context.user_data.get("txn")
    if not txn:
        await update.message.reply_text("Send /pay <TXN_ID> first!")
        return
    if not update.message.photo:
        await update.message.reply_text("Send a photo screenshot of your payment.")
        return

    used_txn.add(txn)

    # Forward to admin with approve/reject buttons
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ])

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"Payment from {update.effective_user.full_name}\nUserID: {user_id}\nTXN: {txn}",
        reply_markup=keyboard
    )

    await update.message.reply_text("Screenshot sent to admin for approval.")

# Callback handler for admin buttons
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_caption("❌ Unauthorized")
        return

    if action == "approve":
        paid_users[user_id] = True
        await context.bot.send_message(chat_id=user_id, text="🎉 Your premium access is now active!")
        await query.edit_message_caption("✅ Approved by admin")
    elif action == "reject":
        await context.bot.send_message(chat_id=user_id, text="❌ Payment rejected by admin")
        await query.edit_message_caption("❌ Rejected by admin")

# /premium command to check status
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if paid_users.get(user_id):
        await update.message.reply_text("🎬 You are premium!")
    else:
        await update.message.reply_text("❌ You are not premium. Use /buy")

# Setup application
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("pay", pay))
app.add_handler(MessageHandler(filters.PHOTO, screenshot))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CommandHandler("premium", premium))

print("Bot is running...")
app.run_polling()
