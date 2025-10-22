"""
Обробник команди /translate - Перекладач
"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response, transcribe_audio
from utils.constants import CHOOSING_LANGUAGE, TRANSLATING, LANGUAGES

logger = logging.getLogger(__name__)


async def translate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Початок перекладача – вибір мови"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) натиснув /translate")

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
                caption="🌍 Перекладач\n\nВибери мову, якою потрібно перекласти:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "🌍 Перекладач\n\nВибери мову, якою потрібно перекласти:",
            reply_markup=reply_markup
        )

    return CHOOSING_LANGUAGE


async def translate_choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Користувач вибрав мову"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    lang_key = query.data.replace("translate_lang_", "")
    language = LANGUAGES.get(lang_key)

    if not language:
        await query.message.reply_text("Помилка вибору мови. Спробуй /translate ще раз.")
        return ConversationHandler.END

    context.user_data['translate_language'] = language
    context.user_data['translate_lang_key'] = lang_key

    logger.info(f"Користувач {user.first_name} ({user.id}) вибрав мову {language['name']}")

    await query.message.reply_text(
        f"{language['emoji']} Мова перекладу: {language['name']}\n\n"
        f"Тепер відправь мені:\n"
        f"• Текстове повідомлення для перекладу\n"
        f"• АБО голосове повідомлення 🎤"
    )

    return TRANSLATING


async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перекладає текстове повідомлення"""
    user = update.effective_user
    text = update.message.text

    language = context.user_data.get('translate_language')

    if not language:
        await update.message.reply_text("Помилка: мова не вибрана. Почни заново з /translate")
        return ConversationHandler.END

    logger.info(f"Користувач {user.first_name} ({user.id}) надіслав текст для перекладу: {text}")

    await update.message.reply_text("⏳ Перекладаю...")

    prompt = f"Переклади наступний текст на {language['name']} мову. Виведи ТІЛЬКИ переклад, без коментарів:\n\n{text}"
    translation = get_chatgpt_response(prompt)

    keyboard = [
        [InlineKeyboardButton("🔄 Змінити мову", callback_data="translate_change_lang")],
        [InlineKeyboardButton("❌ Закінчити", callback_data="translate_end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{language['emoji']} Переклад на {language['name']}:\n\n{translation}",
        reply_markup=reply_markup
    )

    logger.info(f"Переклад надіслано користувачу {user.first_name} ({user.id})")

    return TRANSLATING


async def translate_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перекладає голосове повідомлення"""
    user = update.effective_user

    language = context.user_data.get('translate_language')

    if not language:
        await update.message.reply_text("Помилка: мова не вибрана. Почни заново з /translate")
        return ConversationHandler.END

    logger.info(f"Користувач {user.first_name} ({user.id}) надіслав голос для перекладу")

    await update.message.reply_text("🎤 Обробляю голосове повідомлення...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        os.makedirs("temp", exist_ok=True)

        voice_path = f"temp/translate_voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        text = transcribe_audio(voice_path)

        if text.startswith("Помилка"):
            await update.message.reply_text(f"❌ {text}")
            os.remove(voice_path)
            return TRANSLATING

        logger.info(f"Розпізнаний текст: {text}")
        await update.message.reply_text(f"📝 Розпізнано: {text}\n\n⏳ Перекладаю...")

        prompt = f"Переклади наступний текст на {language['name']} мову. Виведи ТІЛЬКИ переклад, без коментарів:\n\n{text}"
        translation = get_chatgpt_response(prompt)

        keyboard = [
            [InlineKeyboardButton("🔄 Змінити мову", callback_data="translate_change_lang")],
            [InlineKeyboardButton("❌ Закінчити", callback_data="translate_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"{language['emoji']} Переклад на {language['name']}:\n\n{translation}",
            reply_markup=reply_markup
        )

        logger.info(f"Переклад голосу надіслано користувачу {user.first_name} ({user.id})")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Помилка обробки голосу для перекладу: {str(e)}")
        await update.message.reply_text(f"❌ Помилка обробки: {str(e)}")

    return TRANSLATING


async def translate_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання кнопок у перекладачі"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == "translate_change_lang":
        logger.info(f"Користувач {user.first_name} ({user.id}) змінює мову перекладу")

        keyboard = []
        for key, lang in LANGUAGES.items():
            keyboard.append([InlineKeyboardButton(
                f"{lang['emoji']} {lang['name']}",
                callback_data=f"translate_lang_{key}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            "🌍 Вибери нову мову для перекладу:",
            reply_markup=reply_markup
        )

        return CHOOSING_LANGUAGE

    elif query.data == "translate_end":
        language = context.user_data.get('translate_language')

        logger.info(f"Користувач {user.first_name} ({user.id}) завершив переклад.")

        if language:
            await query.message.reply_text(
                "👋 Переклад завершено!\n\n"
                "Використовуйте /translate щоб почати знову або /start для головного меню."
            )
        else:
            await query.message.reply_text(
                "Переклад завершено! Використовуйте /start для головного меню."
            )

        context.user_data.clear()

        return ConversationHandler.END
