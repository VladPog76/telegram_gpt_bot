
"""
Базові команди: /start, /help
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) натиснув /start")
    await update.message.reply_text(
        f"Привіт, {user.first_name}! 🤖\n\n"
        "Я бот з ChatGPT!\n"
        "Команди:\n"
        "/start — розпочати\n"
        "/help — допомога\n"
        "/gpt — задати питання ChatGPT\n"
        "/random — випадковий цікавий факт\n"
        "/talk — поговорити з відомою особою\n"
        "/quiz — пограти в квіз\n"
        "/translate — перекладач тексту та голосу"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) натиснув /help")
    await update.message.reply_text(
        "📖 Довідка по командах:\n\n"
        "/start — головне меню\n"
        "/help — ця довідка\n"
        "/gpt — задати питання ChatGPT\n"
        "/random — отримати випадковий цікавий факт\n"
        "/talk — поговорити з відомою особою\n"
        "/quiz — пограти в квіз\n"
        "/translate — перекласти текст або голос\n\n"
        "🎤 Голосовий режим:\n"
        "Просто відправ мені голосове повідомлення,\n"
        "і я відповім тобі голосом!"
    )
