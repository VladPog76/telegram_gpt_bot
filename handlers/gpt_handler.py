"""
Оброблювач команди /gpt - ChatGPT інтерфейс
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response
from utils.constants import WAITING_GPT_QUESTION

logger = logging.getLogger(__name__)


async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Початок роботи с ChatGPT"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) натиснув /gpt")

    try:
        with open('images/gpt.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🤖 ChatGPT інтерфейс\n\nНапиши своє запитання текстом або надішліть голосове повідомлення 🎤"
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🤖 ChatGPT Інтерфейс\n\nНапиши своє запитання текстом або надішліть голосове повідомлення 🎤"
        )

    return WAITING_GPT_QUESTION


async def gpt_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отримуємо питання та відправляємо до ChatGPT"""
    user = update.effective_user
    user_message = update.message.text

    logger.info(f"Користувач {user.first_name} ({user.id}) надіслав питання: {user_message}")

    await update.message.reply_text("⏳ Обробляю запит...")

    response = get_chatgpt_response(user_message)

    keyboard = [
        [InlineKeyboardButton("➕ Ще питання", callback_data="gpt_more")],
        [InlineKeyboardButton("❌ Закінчити", callback_data="gpt_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup)

    logger.info(f"Відповідь надіслано користувачу {user.first_name} ({user.id})")

    return WAITING_GPT_QUESTION


async def gpt_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання на кнопки /gpt"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "gpt_more":
        logger.info(f"Користувач {user.first_name} ({user.id}) хоче поставити ще питання")

        await query.message.reply_text(
            "🤖 ChatGPT готовий до нового питання!\n\n"
            "Напиши своє запитання:"
        )

        return WAITING_GPT_QUESTION

    elif query.data == "gpt_end":
        logger.info(f"Користувач {user.first_name} ({user.id}) закінчив /gpt")

        await query.message.reply_text(
            "👋 Повертайся з питаннями ще!\n\n"
            "Використовуйте /start для виклику головного меню."
        )

        return ConversationHandler.END


async def gpt_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє голосове повідомлення у режимі /gpt"""
    import os
    from utils.openai_helper import transcribe_audio

    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) надіслав голос в /gpt")

    await update.message.reply_text("🎤 Обробляю голосове повідомлення...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        os.makedirs("temp", exist_ok=True)

        voice_path = f"temp/gpt_voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        text = transcribe_audio(voice_path)

        if text.startswith("Помилка"):
            await update.message.reply_text(f"❌ {text}")
            os.remove(voice_path)
            return WAITING_GPT_QUESTION

        logger.info(f"Розпізнаний текст у /gpt: {text}")
        await update.message.reply_text(f"📝 Ти сказав: {text}\n\n⏳ Обробляю запит...")

        response = get_chatgpt_response(text)

        keyboard = [
            [InlineKeyboardButton("➕ Ще питання", callback_data="gpt_more")],
            [InlineKeyboardButton("❌ Закінчити", callback_data="gpt_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(response, reply_markup=reply_markup)

        logger.info(f"Відповідь надіслано користувачу{user.first_name} ({user.id})")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Помилка обробки голосу в /gpt: {str(e)}")
        await update.message.reply_text(f"❌ Помилка обробки: {str(e)}")

    return WAITING_GPT_QUESTION