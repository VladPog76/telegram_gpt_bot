"""
Обработчик команды /translate - Переводчик
"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response, transcribe_audio
from utils.constants import CHOOSING_LANGUAGE, TRANSLATING, LANGUAGES

logger = logging.getLogger(__name__)


async def translate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало переводчика - выбор языка"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) вызвал /translate")

    keyboard = []
    for key, lang in LANGUAGES.items():
        keyboard.append([InlineKeyboardButton(
            f"{lang['emoji']} {lang['name']}",
            callback_data=f"translate_lang_{key}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open('images/translate.jpg', 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption="🌍 Переводчик\n\nВыбери язык, на который нужно перевести:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🌍 Переводчик\n\nВыбери язык, на который нужно перевести:",
            reply_markup=reply_markup
        )

    return CHOOSING_LANGUAGE


async def translate_choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь выбрал язык"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    lang_key = query.data.replace("translate_lang_", "")
    language = LANGUAGES.get(lang_key)

    if not language:
        await query.message.reply_text("Ошибка выбора языка. Попробуй /translate снова.")
        return ConversationHandler.END

    context.user_data['translate_language'] = language
    context.user_data['translate_lang_key'] = lang_key

    logger.info(f"Пользователь {user.first_name} ({user.id}) выбрал язык {language['name']}")

    await query.message.reply_text(
        f"{language['emoji']} Язык перевода: {language['name']}\n\n"
        f"Теперь отправь мне:\n"
        f"• Текстовое сообщение для перевода\n"
        f"• ИЛИ голосовое сообщение 🎤"
    )

    return TRANSLATING


async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переводит текстовое сообщение"""
    user = update.effective_user
    text = update.message.text

    language = context.user_data.get('translate_language')

    if not language:
        await update.message.reply_text("Ошибка: язык не выбран. Начни заново с /translate")
        return ConversationHandler.END

    logger.info(f"Пользователь {user.first_name} ({user.id}) отправил текст для перевода: {text}")

    await update.message.reply_text("⏳ Перевожу...")

    prompt = f"Переведи следующий текст на {language['name']} язык. Выведи ТОЛЬКО перевод, без комментариев:\n\n{text}"
    translation = get_chatgpt_response(prompt)

    keyboard = [
        [InlineKeyboardButton("🔄 Сменить язык", callback_data="translate_change_lang")],
        [InlineKeyboardButton("❌ Закончить", callback_data="translate_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{language['emoji']} Перевод на {language['name']}:\n\n{translation}",
        reply_markup=reply_markup
    )

    logger.info(f"Перевод отправлен пользователю {user.first_name} ({user.id})")

    return TRANSLATING


async def translate_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переводит голосовое сообщение"""
    user = update.effective_user

    language = context.user_data.get('translate_language')

    if not language:
        await update.message.reply_text("Ошибка: язык не выбран. Начни заново с /translate")
        return ConversationHandler.END

    logger.info(f"Пользователь {user.first_name} ({user.id}) отправил голос для перевода")

    await update.message.reply_text("🎤 Обрабатываю голосовое сообщение...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        os.makedirs("temp", exist_ok=True)

        voice_path = f"temp/translate_voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        text = transcribe_audio(voice_path)

        if text.startswith("Ошибка"):
            await update.message.reply_text(f"❌ {text}")
            os.remove(voice_path)
            return TRANSLATING

        logger.info(f"Распознанный текст: {text}")
        await update.message.reply_text(f"📝 Распознано: {text}\n\n⏳ Перевожу...")

        prompt = f"Переведи следующий текст на {language['name']} язык. Выведи ТОЛЬКО перевод, без комментариев:\n\n{text}"
        translation = get_chatgpt_response(prompt)

        keyboard = [
            [InlineKeyboardButton("🔄 Сменить язык", callback_data="translate_change_lang")],
            [InlineKeyboardButton("❌ Закончить", callback_data="translate_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"{language['emoji']} Перевод на {language['name']}:\n\n{translation}",
            reply_markup=reply_markup
        )

        logger.info(f"Перевод голоса отправлен пользователю {user.first_name} ({user.id})")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Ошибка обработки голоса для перевода: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")

    return TRANSLATING


async def translate_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки в переводчике"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "translate_change_lang":
        logger.info(f"Пользователь {user.first_name} ({user.id}) меняет язык перевода")

        keyboard = []
        for key, lang in LANGUAGES.items():
            keyboard.append([InlineKeyboardButton(
                f"{lang['emoji']} {lang['name']}",
                callback_data=f"translate_lang_{key}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "🌍 Выбери новый язык для перевода:",
            reply_markup=reply_markup
        )

        return CHOOSING_LANGUAGE

    elif query.data == "translate_end":
        language = context.user_data.get('translate_language')

        logger.info(f"Пользователь {user.first_name} ({user.id}) завершил переводчик")

        if language:
            await query.message.reply_text(
                "👋 Переводчик завершен!\n\n"
                "Используй /translate чтобы начать снова или /start для главного меню."
            )
        else:
            await query.message.reply_text(
                "Переводчик завершен! Используй /start для главного меню."
            )

        context.user_data.clear()

        return ConversationHandler.END