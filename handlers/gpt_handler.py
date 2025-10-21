"""
Обработчик команды /gpt - ChatGPT интерфейс
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response
from utils.constants import WAITING_GPT_QUESTION

logger = logging.getLogger(__name__)


async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ChatGPT"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /gpt")

    try:
        with open('images/gpt.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🤖 ChatGPT интерфейс\n\nНапиши свой вопрос текстом или отправь голосовое сообщение 🎤"
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🤖 ChatGPT интерфейс\n\nНапиши свой вопрос текстом или отправь голосовое сообщение 🎤"
        )

    return WAITING_GPT_QUESTION


async def gpt_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем вопрос и отправляем в ChatGPT"""
    user = update.effective_user
    user_message = update.message.text

    logger.info(f"Пользователь {user.first_name} ({user.id}) отправил вопрос: {user_message}")

    await update.message.reply_text("⏳ Обрабатываю запрос...")

    response = get_chatgpt_response(user_message)

    keyboard = [
        [InlineKeyboardButton("➕ Еще вопрос", callback_data="gpt_more")],
        [InlineKeyboardButton("❌ Закончить", callback_data="gpt_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup)

    logger.info(f"Ответ отправлен пользователю {user.first_name} ({user.id})")

    return WAITING_GPT_QUESTION


async def gpt_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в /gpt"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "gpt_more":
        logger.info(f"Пользователь {user.first_name} ({user.id}) хочет задать еще вопрос")

        await query.message.reply_text(
            "🤖 ChatGPT готов к новому вопросу!\n\n"
            "Напиши свой вопрос:"
        )

        return WAITING_GPT_QUESTION

    elif query.data == "gpt_end":
        logger.info(f"Пользователь {user.first_name} ({user.id}) закончил /gpt")

        await query.message.reply_text(
            "👋 Возвращайся с вопросами еще!\n\n"
            "Используй /start для главного меню."
        )

        return ConversationHandler.END


async def gpt_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает голосовое сообщение в режиме /gpt"""
    import os
    from utils.openai_helper import transcribe_audio

    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) отправил голос в /gpt")

    await update.message.reply_text("🎤 Обрабатываю голосовое сообщение...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        os.makedirs("temp", exist_ok=True)

        voice_path = f"temp/gpt_voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        text = transcribe_audio(voice_path)

        if text.startswith("Ошибка"):
            await update.message.reply_text(f"❌ {text}")
            os.remove(voice_path)
            return WAITING_GPT_QUESTION

        logger.info(f"Распознанный текст в /gpt: {text}")
        await update.message.reply_text(f"📝 Ты сказал: {text}\n\n⏳ Обрабатываю запрос...")

        response = get_chatgpt_response(text)

        keyboard = [
            [InlineKeyboardButton("➕ Еще вопрос", callback_data="gpt_more")],
            [InlineKeyboardButton("❌ Закончить", callback_data="gpt_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(response, reply_markup=reply_markup)

        logger.info(f"Ответ отправлен пользователю {user.first_name} ({user.id})")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Ошибка обработки голоса в /gpt: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")

    return WAITING_GPT_QUESTION