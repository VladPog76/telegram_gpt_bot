
import os
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

# Отримуємо токени
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_TOKEN = os.getenv('OPENAI_TOKEN')
PROXY = os.getenv('PROXY')  # Додали проксі

# Перевірка, що токени завантажені
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не знайдено в .env файлі!")

if not OPENAI_TOKEN:
    raise ValueError("OPENAI_TOKEN не знайдено в .env файлі!")

# Проксі опціональний, тому не вимагаємо його
