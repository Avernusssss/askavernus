from aiogram import F, Router
from aiogram.filters import Command, StateFilter, Text
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

import os
import logging

from handlers.common import BotStates, get_main_keyboard
from services.ai_service import AIService
from utils.message_utils import send_long_message

# Создание логгера
logger = logging.getLogger(__name__)

# Создание роутера
router = Router()

@router.message(F.text == "📜 История")
async def history_button(message: Message, db):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        await message.answer("У вас нет прав для просмотра истории")
        return
        
    try:
        history = db.get_all_history(limit=10)
        
        MAX_MESSAGE_LENGTH = 4000
        current_response = "📜 Последние сообщения:\n\n"
        
        for user_id, username, msg, resp, timestamp, chat_id in history:
            entry = f"👤 {username} (ID: {user_id})\n"
            entry += f"⏰ Time: {timestamp}\n"
            entry += f"💭 Message: {msg}\n"
            
            if len(resp) > 500:
                resp = resp[:500] + "... (сообщение обрезано)"
                
            entry += f"🤖 Response: {resp}\n"
            entry += "➖" * 20 + "\n\n"
            
            if len(current_response) + len(entry) > MAX_MESSAGE_LENGTH:
                await message.answer(current_response)
                current_response = entry
            else:
                current_response += entry
        
        if current_response:
            await message.answer(current_response)
    
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        await message.answer("Ошибка при получении истории")

@router.message(Command('models'), flags={"always": True})
async def models_command(message: Message, ai_service: AIService):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
    
    try:    
        await message.answer("Получаю список доступных моделей...")
        models = await ai_service.get_available_models()
        
        if models:
            response = "📋 Доступные модели:\n\n"
            for model in models:
                response += f"• {model}\n"
            await message.answer(response)
        else:
            await message.answer("Не удалось получить список моделей")
    
    except Exception as e:
        logger.error(f"Error fetching models: {e}", exc_info=True)
        await message.answer("Ошибка при получении списка моделей")

@router.message(F.text == "🤖 Модели AI")
async def ai_models_button(message: Message, state: FSMContext, ai_service: AIService):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
    
    # Сохраняем предыдущее состояние, чтобы вернуться к нему после выбора модели
    current_state = await state.get_state()
    await state.update_data(previous_state=current_state)
    
    try:    
        await message.answer("Получаю список доступных моделей...")
        models = await ai_service.get_available_models()
        
        if not models:
            await message.answer("Не удалось получить список моделей")
            return
        
        # Создаем клавиатуру с моделями
        keyboard = []
        current_model = ai_service.get_current_model()
        
        for model in models:
            # Отмечаем текущую модель звездочкой
            model_text = f"✅ {model}" if model == current_model else model
            keyboard.append([KeyboardButton(text=model_text)])
        
        # Добавляем кнопку возврата
        keyboard.append([KeyboardButton(text="◀️ Назад")])
        
        reply_markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        await message.answer(
            f"Текущая модель: {current_model}\n\n"
            "Выберите модель для использования:",
            reply_markup=reply_markup
        )
        
        # Устанавливаем состояние выбора модели
        await state.set_state(BotStates.ChooseModel)
    
    except Exception as e:
        logger.error(f"Error showing AI models: {e}", exc_info=True)
        await message.answer("Ошибка при получении списка моделей")

@router.message(StateFilter(BotStates.ChooseModel))
async def process_model_selection(message: Message, state: FSMContext, ai_service: AIService):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        await state.clear()
        return
    
    try:
        # Получаем данные о предыдущем состоянии
        data = await state.get_data()
        previous_state = data.get('previous_state')
        
        if message.text == "◀️ Назад":
            # Возвращаемся к предыдущему состоянию, если оно было
            if previous_state:
                await state.set_state(previous_state)
            else:
                await state.clear()
                
            await message.answer(
                "Возвращаемся в предыдущее меню",
                reply_markup=get_main_keyboard(message)
            )
            return
        
        # Удаляем отметку текущей модели, если она есть
        selected_model = message.text
        if selected_model.startswith("✅ "):
            selected_model = selected_model[2:].strip()
        
        # Проверяем, существует ли такая модель
        models = await ai_service.get_available_models()
        if selected_model not in models:
            await message.answer(
                f"Модель '{selected_model}' не найдена. Пожалуйста, выберите из списка.",
                reply_markup=get_main_keyboard(message)
            )
            
            # Возвращаемся к предыдущему состоянию
            if previous_state:
                await state.set_state(previous_state)
            else:
                await state.clear()
                
            return
        
        # Устанавливаем новую модель
        ai_service.set_current_model(selected_model)
        
        await message.answer(
            f"Модель успешно изменена на: {selected_model}",
            reply_markup=get_main_keyboard(message)
        )
        
        # Возвращаемся к предыдущему состоянию
        if previous_state:
            await state.set_state(previous_state)
        else:
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error selecting model: {e}", exc_info=True)
        await message.answer("Ошибка при выборе модели")
        await state.clear()