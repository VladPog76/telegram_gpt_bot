
"""
Обробник команди /translate - Перекладач
"""
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.openai_helper import get_chatgpt_response, transcribe_audio, text_to_speech
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
            callback_data=f"lang_{key}"  # ← ВИПРАВЛЕНО! Було translate_lang_
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
    """Обробляє вибір мови"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    language_code = query.data.replace("lang_", "")
    language_name = LANGUAGES[language_code]["name"]

    # Зберігаємо мову
    context.user_data['target_language'] = language_name

    logger.info(f"Користувач {user.first_name} ({user.id}) вибрав мову {language_name}")
    logger.info(f"Збережено в context.user_data: {context.user_data}")

    await query.message.reply_text(
        f"✅ Вибрано мову: {language_name}\n\n"
        f"📝 Тепер надішліть текст або 🎤 голосове повідомлення для перекладу:"
    )

    return TRANSLATING


async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє текстове повідомлення для перекладу"""
    user = update.effective_user
    user_text = update.message.text

    # Діагностика
    logger.info(f"context.user_data: {context.user_data}")

    target_language = context.user_data.get('target_language')

    logger.info(f"target_language: {target_language}")

    if not target_language:
        await update.message.reply_text("❌ Помилка: мова не вибрана. Почніть знову з /translate")
        return ConversationHandler.END

    logger.info(f"Переклад тексту від {user.first_name}: {user_text} -> {target_language}")

    await update.message.reply_text("⏳ Перекладаю...")

    try:
        # Формуємо промпт
        prompt = f"Переклади наступний текст на {target_language}. Надай тільки переклад без пояснень:\n\n{user_text}"

        # Отримуємо переклад
        translation = get_chatgpt_response(prompt)

        # Зберігаємо в кеш для озвучування
        if 'tts_cache' not in context.bot_data:
            context.bot_data['tts_cache'] = {}

        cache_key = f"{user.id}_{update.message.message_id}"
        context.bot_data['tts_cache'][cache_key] = translation

        logger.info(f"Збережено переклад в TTS кеш: {cache_key}")

        # Створюємо кнопки
        keyboard = [
            [
                InlineKeyboardButton("🔊 Озвучити переклад", callback_data=f"tts_trans_{cache_key}"),
                InlineKeyboardButton("🔄 Ще переклад", callback_data="translate_continue")
            ],
            [InlineKeyboardButton("❌ Закінчити", callback_data="translate_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Відправляємо з кнопками
        await update.message.reply_text(
            f"🌍 Переклад:\n{translation}",
            reply_markup=reply_markup
        )

        logger.info(f"Переклад надіслано користувачу {user.first_name} ({user.id})")

    except Exception as e:
        logger.error(f"Помилка перекладу: {e}")
        await update.message.reply_text(f"❌ Помилка: {e}")

    return TRANSLATING


async def translate_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє голосове повідомлення для перекладу"""
    user = update.effective_user
    target_language = context.user_data.get('target_language')

    if not target_language:
        await update.message.reply_text("❌ Помилка: мова не вибрана. Почніть знову з /translate")
        return ConversationHandler.END

    logger.info(f"Користувач {user.first_name} ({user.id}) надіслав голос для перекладу")

    await update.message.reply_text("🎤 Обробляю голосове повідомлення...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        os.makedirs("temp", exist_ok=True)

        voice_path = f"temp/translate_voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        # Розпізнаємо текст
        text = transcribe_audio(voice_path)

        if text.startswith("Помилка"):
            await update.message.reply_text(f"❌ {text}")
            os.remove(voice_path)
            return TRANSLATING

        logger.info(f"Розпізнаний текст: {text}")
        await update.message.reply_text(f"📝 Ти сказав: {text}\n\n⏳ Перекладаю...")

        # Формуємо промпт
        prompt = f"Переклади наступний текст на {target_language}. Надай тільки переклад без пояснень:\n\n{text}"

        # Отримуємо переклад
        translation = get_chatgpt_response(prompt)

        # Зберігаємо в кеш для озвучування
        if 'tts_cache' not in context.bot_data:
            context.bot_data['tts_cache'] = {}

        cache_key = f"{user.id}_{update.message.message_id}"
        context.bot_data['tts_cache'][cache_key] = translation

        logger.info(f"Збережено переклад в TTS кеш: {cache_key}")

        # Створюємо кнопки
        keyboard = [
            [
                InlineKeyboardButton("🔊 Озвучити переклад", callback_data=f"tts_trans_{cache_key}"),
                InlineKeyboardButton("🔄 Ще переклад", callback_data="translate_continue")
            ],
            [InlineKeyboardButton("❌ Закінчити", callback_data="translate_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Відправляємо з кнопками
        await update.message.reply_text(
            f"🌍 Переклад:\n{translation}",
            reply_markup=reply_markup
        )

        logger.info(f"Переклад голосу надіслано користувачу {user.first_name} ({user.id})")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Помилка обробки голосу для перекладу: {e}")
        await update.message.reply_text(f"❌ Помилка: {e}")
        if os.path.exists(voice_path):
            os.remove(voice_path)

    return TRANSLATING


async def translate_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка кнопок у режимі перекладу"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    logger.info(f"Користувач {user.first_name} натиснув кнопку: {query.data}")

    # Озвучування перекладу
    if query.data.startswith('tts_trans_'):
        cache_key = query.data.replace('tts_trans_', '')

        tts_cache = context.bot_data.get('tts_cache', {})

        if cache_key not in tts_cache:
            await query.message.reply_text("❌ Текст для озвучування не знайдено")
            return TRANSLATING

        text_to_voice = tts_cache[cache_key]

        await query.message.reply_text("🎙️ Створюю аудіо перекладу...")

        output_path = f"temp/tts_trans_{user.id}_{cache_key}.mp3"

        try:
            os.makedirs("temp", exist_ok=True)

            if text_to_speech(text_to_voice, output_path):
                with open(output_path, 'rb') as audio_file:
                    await query.message.reply_voice(voice=audio_file)

                os.remove(output_path)
                del tts_cache[cache_key]

                # Кнопки після озвучування
                keyboard = [
                    [InlineKeyboardButton("🔄 Ще переклад", callback_data="translate_continue")],
                    [InlineKeyboardButton("❌ Закінчити", callback_data="translate_end")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.message.reply_text(
                    "🎙️ Озвучування завершено!\nЩо далі?",
                    reply_markup=reply_markup
                )
            else:
                await query.message.reply_text("❌ Помилка при створенні аудіо")

        except Exception as e:
            logger.error(f"Помилка TTS в перекладі: {e}")
            await query.message.reply_text(f"❌ Помилка: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)

        return TRANSLATING

    # Ще переклад
    elif query.data == "translate_continue":
        await query.message.reply_text(
            "📝 Надішліть текст або голосове для перекладу:"
        )
        return TRANSLATING

    # Закінчити
    elif query.data == "translate_end":
        await query.message.reply_text(
            "👋 Дякую за використання перекладача!\n"
            "Щоб повернутися - /start"
        )
        return ConversationHandler.END

    return TRANSLATING
