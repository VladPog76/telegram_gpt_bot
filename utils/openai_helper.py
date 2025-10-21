
import logging
from openai import OpenAI
from config import OPENAI_TOKEN





# Инициализируем клиент OpenAI
client = OpenAI(api_key=OPENAI_TOKEN)


def get_chatgpt_response(user_message: str, system_prompt: str = None) -> str:
    """
    Отправляет запрос в ChatGPT и возвращает ответ

    Args:
        user_message: Сообщение пользователя
        system_prompt: Системный промпт (опционально)

    Returns:
        Ответ от ChatGPT
    """
    try:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка OpenAI API: {str(e)}")
        return "Извините, произошла ошибка при обращении к ChatGPT. Попробуйте позже."


def get_chatgpt_response_with_history(messages: list) -> str:
    """
    Отправляет запрос в ChatGPT с историей диалога

    Args:
        messages: Список сообщений в формате [{"role": "...", "content": "..."}]

    Returns:
        Ответ от ChatGPT
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.9
        )

        return response.choices[0].message.content

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка OpenAI API с историей: {str(e)}")
        return "Извините, произошла ошибка при обращении к ChatGPT. Попробуйте позже."


def transcribe_audio(audio_file_path: str) -> str:
    """
    Преобразует аудио в текст с помощью Whisper API

    Args:
        audio_file_path: Путь к аудиофайлу

    Returns:
        Распознанный текст
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"
            )
        return transcript.text
    except FileNotFoundError:
        return "Ошибка: аудиофайл не найден"
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка Whisper API: {str(e)}")
        return "Извините, не удалось распознать аудио. Попробуйте еще раз."


def text_to_speech(text: str, output_path: str) -> bool:
    """
    Преобразует текст в речь с помощью TTS API

    Args:
        text: Текст для озвучки
        output_path: Путь для сохранения аудиофайла

    Returns:
        True если успешно, False если ошибка
    """
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text
        )

        response.stream_to_file(output_path)
        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка TTS API: {str(e)}")
        return False
