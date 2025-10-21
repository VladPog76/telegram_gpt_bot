
"""
Базовые команды: /start, /help
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /start")
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🤖\n\n"
        "Я бот с ChatGPT!\n"
        "Команды:\n"
        "/start — начать\n"
        "/help — помощь\n"
        "/gpt — задать вопрос ChatGPT\n"
        "/random — случайный интересный факт\n"
        "/talk — поговорить с известной личностью\n"
        "/quiz — сыграть в квиз\n"
        "/translate — переводчик текста и голоса"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /help")
    await update.message.reply_text(
        "📖 Справка по командам:\n\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/gpt — задать вопрос ChatGPT\n"
        "/random — получить случайный факт\n"
        "/talk — поговорить с известной личностью\n"
        "/quiz — сыграть в квиз\n"
        "/translate — перевести текст или голос\n\n"
        "🎤 Голосовой режим:\n"
        "Просто отправь мне голосовое сообщение (кружочек),\n"
        "и я отвечу тебе голосом!"
    )