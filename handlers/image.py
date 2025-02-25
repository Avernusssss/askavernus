from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import logging

from handlers.common import BotStates
from services.ai_service import AIService
from services.translator import translate_text

# Создание логгера
logger = logging.getLogger(__name__)

# Создание роутера
router = Router()

@router.message(F.text == "🎨 Картинка")
async def image_button(message: Message, state: FSMContext):
    await message.answer("Че нарисовать?")
    await state.set_state(BotStates.Img)

@router.message(StateFilter(BotStates.Img))
async def send_image(message: Message, ai_service: AIService):
    try:
        user_id = message.from_user.id
        user_input = await translate_text(str(message.text))
        msg = await message.answer("Нужно вдохновение, пажжи")
        
        # Генерируем изображение
        response = await ai_service.generate_image(user_input)
        await msg.edit_text(f"На:\n{response.data[0].url}")
        
    except Exception as e:
        logger.error(f"Error in image generation: {e}", exc_info=True)
        await message.answer("Вдохновения нет...") 