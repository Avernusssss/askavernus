import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import Database
from services.ai_service import AIService
from handlers import common, chat, image, admin

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация базы данных
db = Database('bot_history.db')

# Инициализация сервиса AI
ai_service = AIService(os.getenv("MNN_API_KEY"))

# Регистрация роутеров
dp.include_router(common.router)
dp.include_router(chat.router)
dp.include_router(image.router)
dp.include_router(admin.router)

# Middleware для внедрения зависимостей
@dp.update.middleware()
async def dependencies_middleware(handler, event, data):
    data["db"] = db
    data["ai_service"] = ai_service
    return await handler(event, data)

async def main():
    logger.info("Starting bot")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
