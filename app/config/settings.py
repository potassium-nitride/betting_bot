"""
Конфигурационные настройки для Telegram-бота ставок
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []

# База данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///betting_bot.db')

# Настройки ставок
MIN_BET_AMOUNT = float(os.getenv('MIN_BET_AMOUNT', '10.0'))
MAX_BET_AMOUNT = float(os.getenv('MAX_BET_AMOUNT', '10000.0'))
DEFAULT_ODDS = float(os.getenv('DEFAULT_ODDS', '2.0'))

# Настройки комиссии
HOUSE_EDGE = float(os.getenv('HOUSE_EDGE', '0.05'))  # 5% комиссия дома

# Временные зоны
TIMEZONE = os.getenv('TIMEZONE', 'UTC')

# Настройки для развертывания
PORT = int(os.getenv('PORT', 8000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

# Валидация обязательных настроек
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN должен быть установлен в переменных окружения")

if not ADMIN_IDS:
    print("Предупреждение: ADMIN_IDS не установлены. Админ-функции будут недоступны.")
