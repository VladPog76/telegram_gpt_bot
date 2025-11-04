"""
Оброблювач команди /gpt - ChatGPT інтерфейс
"""
import logging
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from utils.openai_helper import get_chatgpt_response, transcribe_audio, text_to_speech
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
    """Обробка текстового питання до GPT"""
    user = update.effective_user
    user_message = update.message.text

    logger.info(f"GPT питання від {user.first_name}: {user_message}")

    try:
        # Отримуємо відповідь від ChatGPT
        response_text = get_chatgpt_response(user_message)

        # Зберігаємо відповідь для озвучування
        if 'tts_cache' not in context.bot_data:
            context.bot_data['tts_cache'] = {}

        cache_key = f"{user.id}_{update.message.message_id}"
        context.bot_data['tts_cache'][cache_key] = response_text

        # Створюємо клавіатуру з кнопкою озвучування
        keyboard = [
            [
                InlineKeyboardButton("❓ Ще питання", callback_data="gpt_continue"),
                InlineKeyboardButton("🔊 Озвучити", callback_data=f"tts_{cache_key}")
            ],
            [InlineKeyboardButton("❌ Закінчити", callback_data="gpt_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Відправляємо відповідь
        await update.message.reply_text(response_text, reply_markup=reply_markup)

        return WAITING_GPT_QUESTION

    except Exception as e:
        logger.error(f"Помилка в gpt_question: {e}")
        await update.message.reply_text("Вибачте, сталася помилка. Спробуйте ще раз.")
        return WAITING_GPT_QUESTION


async def gpt_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання кнопок у GPT режимі"""
    query = update.callback_query
    await query.answer()  # Обов'язково! Прибирає "годинник"

    user = update.effective_user

    # Логування для діагностики
    logger.info(f"Користувач {user.first_name} натиснув кнопку: {query.data}")

    # Озвучування відповіді
    if query.data.startswith('tts_'):
        cache_key = query.data.replace('tts_', '')

        logger.info(f"Запит озвучування для ключа: {cache_key}")

        # Отримуємо збережений текст
        tts_cache = context.bot_data.get('tts_cache', {})

        logger.info(f"Доступні ключі в кеші: {list(tts_cache.keys())}")

        if cache_key not in tts_cache:
            await query.message.reply_text("❌ Текст для озвучування не знайдено. Можливо, він застарів.")
            logger.warning(f"Ключ {cache_key} не знайдено в кеші")
            return WAITING_GPT_QUESTION

        text_to_voice = tts_cache[cache_key]

        logger.info(f"Знайдено текст довжиною {len(text_to_voice)} символів")

        await query.message.reply_text("🎙️ Створюю аудіо, зачекайте...")

        # Створюємо унікальне ім'я файлу
        output_path = f"temp/tts_{user.id}_{cache_key}.mp3"

        try:
            # Створюємо папку temp якщо немає
            os.makedirs("temp", exist_ok=True)

            logger.info(f"Генерую аудіо в файл: {output_path}")

            # Генеруємо аудіо
            if text_to_speech(text_to_voice, output_path):
                logger.info("Аудіо успішно згенеровано, відправляю...")

                # Відправляємо голосове
                with open(output_path, 'rb') as audio_file:
                    await query.message.reply_voice(voice=audio_file)

                logger.info("Голосове повідомлення відправлено")

                # Видаляємо файл
                os.remove(output_path)
                logger.info("Тимчасовий файл видалено")

                # Видаляємо з кешу
                del tts_cache[cache_key]
                logger.info("Запис видалено з кешу")

                # Додаємо кнопки після озвучування
                keyboard = [
                    [InlineKeyboardButton("❓ Ще питання", callback_data="gpt_continue")],
                    [InlineKeyboardButton("❌ Закінчити", callback_data="gpt_end")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.message.reply_text(
                    "🎙️ Озвучування завершено!\n"
                    "Що далі?",
                    reply_markup=reply_markup
                )
            else:
                await query.message.reply_text("❌ Помилка при створенні аудіо. Перевірте логи OpenAI.")
                logger.error("text_to_speech повернув False")

        except Exception as e:
            logger.error(f"Помилка TTS: {e}", exc_info=True)
            await query.message.reply_text(f"❌ Помилка: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)

        return WAITING_GPT_QUESTION

    # Продовжити діалог
    elif query.data == "gpt_continue":
        await query.message.reply_text("❓ Задайте наступне питання:")
        return WAITING_GPT_QUESTION

    # Закінчити
    elif query.data == "gpt_end":
        await query.message.reply_text(
            "👋 Дякую за спілкування!\n"
            "Щоб повернутися до головного меню - /start"
        )
        return ConversationHandler.END

    # Якщо щось інше
    else:
        logger.warning(f"Невідома callback_data: {query.data}")
        return WAITING_GPT_QUESTION


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

        # Отримуємо відповідь від ChatGPT
        response_text = get_chatgpt_response(text)

        # Зберігаємо відповідь для озвучування
        if 'tts_cache' not in context.bot_data:
            context.bot_data['tts_cache'] = {}

        cache_key = f"{user.id}_{update.message.message_id}"
        context.bot_data['tts_cache'][cache_key] = response_text

        # Логування для перевірки
        logger.info(f"Збережено в TTS кеш: {cache_key}, текст довжиною {len(response_text)} символів")

        # Створюємо клавіатуру з кнопкою озвучування
        keyboard = [
            [
                InlineKeyboardButton("❓ Ще питання", callback_data="gpt_continue"),
                InlineKeyboardButton("🔊 Озвучити", callback_data=f"tts_{cache_key}")
            ],
            [InlineKeyboardButton("❌ Закінчити", callback_data="gpt_end")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Відправляємо відповідь з кнопками
        await update.message.reply_text(response_text, reply_markup=reply_markup)

        logger.info(f"Відповідь надіслано користувачу {user.first_name} ({user.id})")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Помилка обробки голосу в /gpt: {str(e)}")
        await update.message.reply_text(f"❌ Помилка обробки: {str(e)}")

    return WAITING_GPT_QUESTION