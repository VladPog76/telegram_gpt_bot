"""
Оброблювач команди /random - Випадкові факти
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.openai_helper import get_chatgpt_response

logger = logging.getLogger(__name__)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Надсилає випадковий факт від ChatGPT"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) натиснув /random")

    await update.message.reply_text("⏳ Генерую цікавий факт...")

    prompt = "Розкажи один цікавий випадковий факт на будь-яку тему. Будь короткий (2-3 пропозиції) і цікавий."
    fact = get_chatgpt_response(prompt)

    keyboard = [
        [InlineKeyboardButton("🎲 Хочу ще факт", callback_data="random_more")],
        [InlineKeyboardButton("❌ Закінчити", callback_data="random_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open('images/random.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"🎲 Випадковий факт:\n\n{fact}",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            f"🎲 Випадковий факт:\n\n{fact}",
            reply_markup=reply_markup
        )

    logger.info(f"Факт надіслано користувачу {user.first_name} ({user.id})")


async def random_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання на кнопки /random"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "random_more":
        logger.info(f"Користувач {user.first_name} ({user.id}) запросив ще факт")

        await query.message.reply_text("⏳ Генерую ще один факт...")

        prompt = "Розкажи один цікавий випадковий факт на будь-яку тему. Будь короткий (2-3 пропозиції) і цікавий."
        fact = get_chatgpt_response(prompt)

        keyboard = [
            [InlineKeyboardButton("🎲 Хочу ще факт", callback_data="random_more")],
            [InlineKeyboardButton("❌ Закінчити", callback_data="random_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            f"🎲 Випадковий факт:\n\n{fact}",
            reply_markup=reply_markup
        )

    elif query.data == "random_end":
        logger.info(f"Користувач {user.first_name} ({user.id}) закінчив /random")
        await query.message.reply_text("👋 Повертайся за фактами ще!\n\nВикоритовуйте /start для головного меню.")
