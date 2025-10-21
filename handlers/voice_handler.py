"""
Обработчик голосовых сообщений (вне режима переводчика)
"""
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes

from utils.openai_helper import get_chatgpt_response, transcribe_audio, text_to_speech

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает голосовые сообщения"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) отправил голосовое сообщение")

    await update.message.reply_text("🎤 Обрабатываю голосовое сообщение...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        os.makedirs("temp", exist_ok=True)

        voice_path = f"temp/voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        logger.info(f"Голосовое сообщение сохранено: {voice_path}")

        text = transcribe_audio(voice_path)

        if text.startswith("Ошибка"):
            await update.message.reply_text(f"❌ {text}")
            return

        logger.info(f"Распознанный текст: {text}")
        await update.message.reply_text(f"📝 Ты сказал: {text}\n\n⏳ Генерирую ответ...")

        response = get_chatgpt_response(text)

        audio_path = f"temp/response_{user.id}.mp3"

        if text_to_speech(response, audio_path):
            with open(audio_path, 'rb') as audio:
                await update.message.reply_voice(
                    voice=audio,
                    caption=f"🤖 {response}"
                )

            logger.info(f"Голосовой ответ отправлен пользователю {user.first_name} ({user.id})")

            os.remove(audio_path)
        else:
            await update.message.reply_text(f"🤖 {response}")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")