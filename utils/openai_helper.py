
import logging
import httpx
from openai import OpenAI
from config import OPENAI_TOKEN, PROXY

# Ініціалізуємо клієнт OpenAI з проксі
if PROXY:
    # Якщо проксі є - використовуємо
    http_client = httpx.Client(proxy=PROXY)
    client = OpenAI(api_key=OPENAI_TOKEN, http_client=http_client)
    logging.getLogger(__name__).info(f"OpenAI клієнт використовує проксі: {PROXY}")
else:
    # Якщо проксі немає - звичайне підключення
    client = OpenAI(api_key=OPENAI_TOKEN)
    logging.getLogger(__name__).info("OpenAI клієнт працює без проксі")


def get_chatgpt_response(user_message: str, system_prompt: str = None) -> str:
    """
    Надсилає запит до ChatGPT і повертає відповідь

    Args:
        user_message: Повідомлення користувача
        system_prompt: Системний промпт (опціонально)

    Returns:
        Відповідь від ChatGPT
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
        logger.error(f"Помилка OpenAI API: {str(e)}")
        return "Вибачте, виникла помилка при зверненні до ChatGPT. Спробуйте пізніше."


def get_chatgpt_response_with_history(messages: list) -> str:
    """
    Відправляє запит у ChatGPT з історією діалогу

    Args:
        messages: Список повідомлень у форматі [{"role": "...", "content": "..."}]

    Returns:
        Відповідь від ChatGPT
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
        logger.error(f"Помилка OpenAI API з історією: {str(e)}")
        return "Вибачте, виникла помилка при зверненні до ChatGPT. Спробуйте пізніше."


def transcribe_audio(audio_file_path: str) -> str:
    """
    Перетворює аудіо на текст за допомогою Whisper API

    Args:
        audio_file_path: Шлях до аудіофайлу

    Returns:
        Розпізнаний текст
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
        return "Помилка: аудіофайл не знайдено"
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Помилка Whisper API: {str(e)}")
        return "Вибачте, не вдалося розпізнати аудіо. Спробуйте ще раз."


def text_to_speech(text: str, output_path: str) -> bool:
    """
    Перетворює текст на мову за допомогою TTS API

    Args:
        text: Текст для озвучення
        output_path: Шлях для збереження аудіофайлу

    Returns:
        True якщо успішно, False якщо помилка
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
        logger.error(f"Помилка TTS API: {str(e)}")
        return False
