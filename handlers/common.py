from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import os
from functools import lru_cache

# Определение состояний
class BotStates(StatesGroup):
    Chat = State()
    Img = State()
    ChooseModel = State()

# Создание роутера
router = Router()

@lru_cache(maxsize=2)
def get_keyboard(is_admin=False):
    """Создает и кэширует клавиатуру в зависимости от прав пользователя"""
    keyboard = [
        [
            KeyboardButton(text="💬 Чат"),
            KeyboardButton(text="🎨 Картинка"),
        ]
    ]
    
    if is_admin:
        keyboard.extend([
            [
                KeyboardButton(text="📜 История"),
                KeyboardButton(text="🤖 Модели AI")
            ]
        ])
    else:
        keyboard.append([KeyboardButton(text="📜 История")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )

def get_main_keyboard(message):
    """Возвращает клавиатуру в зависимости от прав пользователя"""
    is_admin = message and str(message.from_user.id) == os.getenv("ADMIN_ID")
    return get_keyboard(is_admin)

@router.message(Command('start'))
async def start_command(message: Message):
    await message.answer(
        "Выбирай че те надо, пентюх",
        reply_markup=get_main_keyboard(message)
    )

@router.message(Command('file'))
async def send_last_response_as_file(message: Message, state: FSMContext):
    from utils.message_utils import send_as_file
    
    data = await state.get_data()
    last_response = data.get('last_full_response')
    
    if not last_response:
        await message.answer("Нет сохраненного ответа для отправки.")
        return
    
    await message.answer("Вот полный ответ:")
    await send_as_file(message, last_response, "full_response.txt") 