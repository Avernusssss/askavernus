from mnnai import MNN
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

db = Database('bot_history.db')

mnn_client = MNN(
    key=os.getenv("MNN_API_KEY"),
    max_retries=2,  
    timeout=60,     
    debug=False     
)

class ChoosingBot(StatesGroup):
    Chat = State()
    Img = State()

def get_main_keyboard(message: types.Message) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="💬 Чат"),
            KeyboardButton(text="🎨 Картинка"),
        ]
    ]
    
    if message and str(message.from_user.id) == os.getenv("ADMIN_ID"):
        keyboard.extend([
            [
                KeyboardButton(text="📜 История")
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

@dp.message(F.text == "💬 Чат")
async def chat_button(message: types.Message, state: FSMContext):
    await message.answer("Ну спрашивай, я книжки читал.")
    await state.set_state(ChoosingBot.Chat)
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

@dp.message(StateFilter("ChoosingBot:Chat"))
async def chat_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.full_name
    user_input = message.text
    
    data = await state.get_data()
    chat_id = data.get('chat_id')

    msg = await message.answer("Думаю...")
    full_response = ""
    current_message_text = ""
    MAX_MESSAGE_LENGTH = 4000
    message_parts = []  
    
    try:
        chat_history = db.get_chat_history(user_id, limit=5)
        messages = [{"role": "system", "content": "Ты русскоязычный ассистент."}]
        
        for prev_msg, prev_resp in chat_history:
            messages.append({"role": "user", "content": prev_msg})
            messages.append({"role": "assistant", "content": prev_resp})
        
        messages.append({"role": "user", "content": user_input})

        client = MNN(key=os.getenv("MNN_API_KEY"))
        stream = await client.chat.async_create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                current_message_text += content
                
                if len(current_message_text) >= MAX_MESSAGE_LENGTH:
                    try:
                        await msg.edit_text(current_message_text, parse_mode='Markdown')
                    except:
                        await msg.edit_text(current_message_text)
                    
                    message_parts.append(current_message_text)
                    
                    msg = await message.answer("Продолжение...")
                    current_message_text = ""
                
                elif len(current_message_text) % 20 == 0:
                    try:
                        await msg.edit_text(current_message_text, parse_mode='Markdown')
                    except:
                        await msg.edit_text(current_message_text)
        
        if current_message_text:
            try:
                await msg.edit_text(current_message_text, parse_mode='Markdown')
            except:
                await msg.edit_text(current_message_text)
            
            message_parts.append(current_message_text)
        
        if len(message_parts) > 1:
            await message.answer("Ответ был разбит на несколько частей. Хотите получить полный ответ как файл? Отправьте /file")
            await state.update_data(last_full_response=full_response)
        
        db.add_message(user_id, username, user_input, full_response, chat_id)
        
    except Exception as e:
        print(f"Error in chat: {e}")
        await msg.edit_text(f"Произошла ошибка: {str(e)}")

# image
@dp.message(StateFilter("ChoosingBot:Img"))
async def send_image(message: types.Message):
    user_id = message.from_user.id
    user_input = await (translate_text(str(message.text)))
    msg = await message.answer("Нужно вдохновение, пажжи")
    try:
        client = MNN(key=os.getenv("MNN_API_KEY"))
        response = await client.images.async_create(
            prompt=user_input,
            model="dall-e-3",
            n=1,
            size="1024x1024"
        )
        await msg.edit_text(f"На:\n{response.data[0].url}")
    except Exception as e:
        print("Error in generating image: ", e)
        await msg.edit_text("Вдохновения нет...")

async def translate_text(data: str):
    async with Translator() as translator:
        result = await translator.translate(data, dest='en', src='ru')
        return (result.text)

async def get_available_models():
    try:
        models = mnn_client.GetModels()
        return models
    except Exception as e:
        print(f"Error getting models: {e}")
        return []

@dp.message(Command('models'))
async def models_command(message: types.Message):
    if str(message.from_user.id) != os.getenv("ADMIN_ID"):
        return
        
    await message.answer("Получаю список доступных моделей...")
    models = await get_available_models()
    
    if models:
        response = "📋 Доступные модели:\n\n"
        for model in models:
            response += f"• {model}\n"
        await message.answer(response)
    else:
        await message.answer("Не удалось получить список моделей")

async def send_long_message(message: types.Message, text: str):
    MAX_MESSAGE_LENGTH = 4000  
    
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        part = text[i:i + MAX_MESSAGE_LENGTH]
        await message.answer(part)

async def send_as_file(message: types.Message, text: str, filename="response.txt"):
    """Отправляет длинный текст как файл"""
    from io import BytesIO
    
    bio = BytesIO(text.encode('utf-8'))
    bio.name = filename
    
    await message.answer_document(bio)

@dp.message(Command('file'))
async def send_last_response_as_file(message: types.Message, state: FSMContext):
    data = await state.get_data()
    last_response = data.get('last_full_response')
    
    if not last_response:
        await message.answer("Нет сохраненного ответа для отправки.")
        return
    
    from io import BytesIO
    
    bio = BytesIO(last_response.encode('utf-8'))
    bio.name = "full_response.txt"
    
    await message.answer("Вот полный ответ:")
    await message.answer_document(bio)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
