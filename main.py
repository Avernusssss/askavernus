from g4f import AsyncClient
from googletrans import Translator
from database import Database
import uuid

import logging
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()

# Инициализируем базу данных
db = Database('bot_history.db')

class ChoosingBot(StatesGroup):
    Gpt = State()
    Img = State()
    Mute = State()

# Создаем клавиатуру
def get_main_keyboard(message: types.Message) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="💬 Чат"),
            KeyboardButton(text="🎨 Картинка"),
        ]
    ]
    
    # Добавляем кнопки админа
    if message and str(message.from_user.id) == os.getenv("ADMIN_ID"):
        keyboard.extend([
            [
                KeyboardButton(text="📜 История"),
                KeyboardButton(text="🔇 Мут")
            ]
        ])
    else:
        keyboard.append([KeyboardButton(text="📜 История")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        persistent=True
    )

@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer(
        "Выбирай че те надо, пентюх",
        reply_markup=get_main_keyboard(message)
    )

# Обработчики для кнопок
@dp.message(F.text == "💬 Чат")
async def chat_button(message: types.Message, state: FSMContext):
    await message.answer("Ну спрашивай, я книжки читал.")
    await state.set_state(ChoosingBot.Gpt)
    await state.update_data(chat_id=str(uuid.uuid4()))

@dp.message(F.text == "🎨 Картинка")
async def image_button(message: types.Message, state: FSMContext):
    await message.answer("Че нарисовать?")
    await state.set_state(ChoosingBot.Img)

@dp.message(F.text == "📜 История")
async def history_button(message: types.Message):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        await message.answer("У вас нет прав для просмотра истории")
        return
        
    history = db.get_all_history(limit=10)
    
    response = "📜 Последние сообщения:\n\n"
    for user_id, username, msg, resp, timestamp, chat_id in history:
        response += f"👤 {username} (ID: {user_id})\n"
        response += f"⏰ Time: {timestamp}\n"
        response += f"💭 Message: {msg}\n"
        response += f"🤖 Response: {resp}\n"
        response += "➖" * 20 + "\n\n"
    
    await message.answer(response)

# Добавляем обработчик кнопки мута
@dp.message(F.text == "🔇 Мут")
async def mute_button(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
    
    await message.answer(
        "Отправь ID пользователя и время мута в секундах в формате:\n"
        "ID время\n"
        "Например: 123456789 300"
    )
    await state.set_state(ChoosingBot.Mute)

# Обработчик ввода данных для мута
@dp.message(StateFilter("ChoosingBot:Mute"))
async def process_mute(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
    
    try:
        user_id, duration = map(int, message.text.split())
        db.add_mute(user_id, duration)
        await message.answer(
            f"Пользователь {user_id} замучен на {duration} секунд",
            reply_markup=get_main_keyboard(message)
        )
    except ValueError:
        await message.answer(
            "Неверный формат. Используй: ID время",
            reply_markup=get_main_keyboard(message)
        )
    
    await state.clear()

# ChatGPT
@dp.message(StateFilter("ChoosingBot:Gpt"))
async def send_answer_request(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверяем на мут
    if db.is_muted(user_id):
        await message.answer("Ты в муте, чюдик")
        return
        
    username = message.from_user.full_name  # Получаем полное имя пользователя
    print(f"Новое сообщение от пользователя {username} (ID: {user_id})")
    user_input = message.text
    
    # Получаем chat_id из состояния
    data = await state.get_data()
    chat_id = data.get('chat_id')

    print(user_input)
    msg = await message.answer("Ща пажжи")

    try:
        # Получаем историю последних сообщений
        chat_history = db.get_chat_history(user_id, limit=5)
        messages = [{"role": "system", "content": "Ты русскоязычный ассистент."}]
        
        # Добавляем историю в контекст
        for prev_msg, prev_resp in chat_history:
            messages.append({"role": "user", "content": prev_msg})
            messages.append({"role": "assistant", "content": prev_resp})
        
        # Добавляем текущий запрос
        messages.append({"role": "user", "content": user_input})

        client = AsyncClient()
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            web_search=False
        )

        response_text = response.choices[0].message.content
        
        # Сохраняем сообщение и ответ в базу с именем пользователя
        db.add_message(user_id, username, user_input, response_text, chat_id)
        
        await msg.edit_text(response_text, parse_mode='Markdown')

    except Exception as e:
        print("Error: ", e)
        await msg.edit_text("Ну и хуйню ты сморозил...", parse_mode='Markdown')

# image
@dp.message(StateFilter("ChoosingBot:Img"))
async def send_image(message: types.Message):
    user_id = message.from_user.id
    
    # Проверяем на мут
    if db.is_muted(user_id):
        await message.answer("Ты в муте, чюдик")
        return
        
    user_input = await (translate_text(str(message.text)))
    msg = await message.answer("Нужно вдохновение, пажжи")
    try:
        client = AsyncClient()
        response = await client.images.generate(
            prompt=user_input,
            model="flux",

            response_format="url"
        )
        await msg.edit_text(f"На:\n{response.data[0].url}")
    except Exception as e:
        print("Error in generating image: ", e)
        await msg.edit_text("Вдохновения нет...")

async def translate_text(data: str):
    async with Translator() as translator:
        result = await translator.translate(data, dest='en', src='ru')
        return (result.text)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
