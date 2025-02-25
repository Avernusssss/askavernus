from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters.magic_data import MagicData

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

@router.message(Command('models'), flags={"outer": True})
async def models_command(message: Message, ai_service: AIService, state: FSMContext):
    # Сохраняем текущее состояние
    current_state = await state.get_state()
    
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
    
    # Восстанавливаем состояние
    if current_state:
        await state.set_state(current_state)

@router.message(F.text == "🤖 Модели AI", flags={"outer": True})
async def ai_models_button_high_priority(message: Message, state: FSMContext, ai_service: AIService):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
    
    # Сохраняем текущее состояние
    current_state = await state.get_state()
    logger.info(f"AI Models button pressed. Current state: {current_state}")
    
    # Очищаем состояние для обработки команды
    if current_state:
        await state.clear()
    
    try:    
        await message.answer("Получаю список доступных моделей...")
        models = await ai_service.get_available_models()
        
        if not models:
            await message.answer("Не удалось получить список моделей")
            # Восстанавливаем состояние
            if current_state:
                await state.set_state(current_state)
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
        
        # Сохраняем предыдущее состояние перед установкой нового
        await state.update_data(previous_state=current_state)
        
        # Устанавливаем состояние выбора модели
        await state.set_state(BotStates.ChooseModel)
    
    except Exception as e:
        logger.error(f"Error showing AI models: {e}", exc_info=True)
        await message.answer("Ошибка при получении списка моделей")
        # Восстанавливаем состояние в случае ошибки
        if current_state:
            await state.set_state(current_state)

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
            if previous_state and previous_state in [BotStates.Chat, BotStates.Img]:
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
            if previous_state and previous_state in [BotStates.Chat, BotStates.Img]:
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
        if previous_state and previous_state in [BotStates.Chat, BotStates.Img]:
            await state.set_state(previous_state)
        else:
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error selecting model: {e}", exc_info=True)
        await message.answer("Ошибка при выборе модели")
        await state.clear()

@router.message(F.text == "🤖 Модели AI", MagicData(F.state != BotStates.ChooseModel))
async def global_ai_models_button(message: Message, state: FSMContext, ai_service: AIService):
    # Перенаправляем на основной обработчик
    await ai_models_button(message, state, ai_service)