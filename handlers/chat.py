from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import uuid
import logging

from handlers.common import BotStates, get_main_keyboard
from utils.message_utils import stream_response
from services.ai_service import AIService

# Создание логгера
logger = logging.getLogger(__name__)

# Создание роутера
router = Router()

@router.message(F.text == "💬 Чат")
async def chat_button(message: Message, state: FSMContext):
    await message.answer("Ну спрашивай, я книжки читал.")
    await state.set_state(BotStates.Chat)
    await state.update_data(chat_id=str(uuid.uuid4()))

@router.message(StateFilter(BotStates.Chat))
async def chat_message(message: Message, state: FSMContext, ai_service: AIService, db):
    try:
        user_id = message.from_user.id
        username = message.from_user.full_name
        user_input = message.text
        
        data = await state.get_data()
        chat_id = data.get('chat_id')
        
        # Получаем историю последних сообщений
        chat_history = db.get_chat_history(user_id, limit=5)
        messages = [{"role": "system", "content": "Ты русскоязычный ассистент."}]
        
        # Добавляем историю в контекст
        for prev_msg, prev_resp in chat_history:
            messages.append({"role": "user", "content": prev_msg})
            messages.append({"role": "assistant", "content": prev_resp})
        
        # Добавляем текущий запрос
        messages.append({"role": "user", "content": user_input})
        
        # Получаем стрим ответа
        stream = await ai_service.chat_completion(messages, stream=True)
        
        # Обрабатываем стрим и получаем полный ответ
        full_response, message_parts = await stream_response(message, stream)
        
        # Если ответ был разбит на несколько частей, предлагаем отправить его как файл
        if len(message_parts) > 1:
            await message.answer("Ответ был разбит на несколько частей. Хотите получить полный ответ как файл? Отправьте /file")
            await state.update_data(last_full_response=full_response)
        
        # Сохраняем сообщение и ответ в базу
        db.add_message(user_id, username, user_input, full_response, chat_id)
        
    except Exception as e:
        logger.error(f"Error in chat processing: {e}", exc_info=True)
        await message.answer(f"Произошла ошибка: {str(e)}") 