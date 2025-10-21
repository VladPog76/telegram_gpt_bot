"""
Обработчик команды /random - Случайные факты
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.openai_helper import get_chatgpt_response

logger = logging.getLogger(__name__)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет случайный факт от ChatGPT"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /random")

    await update.message.reply_text("⏳ Генерирую интересный факт...")

    prompt = "Расскажи один интересный случайный факт на любую тему. Будь краток (2-3 предложения) и интересен."
    fact = get_chatgpt_response(prompt)

    keyboard = [
        [InlineKeyboardButton("🎲 Хочу еще факт", callback_data="random_more")],
        [InlineKeyboardButton("❌ Закончить", callback_data="random_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open('images/random.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"🎲 Случайный факт:\n\n{fact}",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            f"🎲 Случайный факт:\n\n{fact}",
            reply_markup=reply_markup
        )

    logger.info(f"Факт отправлен пользователю {user.first_name} ({user.id})")


async def random_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в /random"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "random_more":
        logger.info(f"Пользователь {user.first_name} ({user.id}) запросил еще факт")

        await query.message.reply_text("⏳ Генерирую еще один факт...")

        prompt = "Расскажи один интересный случайный факт на любую тему. Будь краток (2-3 предложения) и интересен."
        fact = get_chatgpt_response(prompt)

        keyboard = [
            [InlineKeyboardButton("🎲 Хочу еще факт", callback_data="random_more")],
            [InlineKeyboardButton("❌ Закончить", callback_data="random_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            f"🎲 Случайный факт:\n\n{fact}",
            reply_markup=reply_markup
        )

    elif query.data == "random_end":
        logger.info(f"Пользователь {user.first_name} ({user.id}) закончил /random")
        await query.message.reply_text("👋 Возвращайся за фактами еще!\n\nИспользуй /start для начала.")
