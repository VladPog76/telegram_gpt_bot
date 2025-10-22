"""
Обробник голосових повідомлень (поза режимом перекладача)
"""
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes

from utils.openai_helper import get_chatgpt_response, transcribe_audio, text_to_speech

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє голосові повідомлення"""
    user = update.effective_user
    logger.info(f"Користувач {user.first_name} ({user.id}) надіслав голосове повідомлення")

    await update.message.reply_text("🎤 Обробляю голосове повідомлення...")

    try:
        voice = update.message.voice
        voice_file = await context.bot.get_file(voice.file_id)

        os.makedirs("temp", exist_ok=True)

        voice_path = f"temp/voice_{user.id}.ogg"
        await voice_file.download_to_drive(voice_path)

        logger.info(f"Голосове повідомлення збережене: {voice_path}")

        text = transcribe_audio(voice_path)

        if text.startswith("Помилка"):
            await update.message.reply_text(f"❌ {text}")
            return

        logger.info(f"Розпізнаний текст: {text}")
        await update.message.reply_text(f"📝 Ти сказав: {text}\n\n⏳ Генерую відповідь...")

        response = get_chatgpt_response(text)

        audio_path = f"temp/response_{user.id}.mp3"

        if text_to_speech(response, audio_path):
            with open(audio_path, 'rb') as audio:
                await update.message.reply_voice(
                    voice=audio,
                    caption=f"🤖 {response}"
                )

            logger.info(f"Голосова відповідь надіслано користувачу {user.first_name} ({user.id})")

            os.remove(audio_path)
        else:
            await update.message.reply_text(f"🤖 {response}")

        os.remove(voice_path)

    except Exception as e:
        logger.error(f"Помилка обробки голосового повідомлення: {str(e)}")
        await update.message.reply_text(f"❌ Помилка обробки: {str(e)}")