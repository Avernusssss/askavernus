from g4f import AsyncClient
from googletrans import Translator

import logging
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()

class ChoosingBot(StatesGroup):
    Gpt = State()
    Img = State()

@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer(
        "Выбирай че те надо, пентюх\n/чат\n/картинка")

@dp.message(Command('чат'))
async def set_state_gpt(message: types.Message, state: FSMContext):
    await message.answer("Ну спрашивай, я книжки читал.")
    await state.set_state(ChoosingBot.Gpt)

@dp.message(Command('картинка'))
async def set_state_gpt(message: types.Message, state: FSMContext):
    await message.answer("Че нарисовать?")
    await state.set_state(ChoosingBot.Img)

# ChatGPT
@dp.message(StateFilter("ChoosingBot:Gpt"))
async def send_answer_request(message: types.Message):
    user_id = message.from_user.id
    user_input = message.text

    print(user_input)
    msg = await message.answer("Ща пажжи")

    try:
        client = AsyncClient()
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": user_input}],
            web_search=False

        )

        await msg.edit_text(response.choices[0].message.content, parse_mode='Markdown')

    except Exception as e:
        print("Error: ", e)
        await msg.edit_text("Ну и хуйню ты сморозил...", parse_mode='Markdown')

# image
@dp.message(StateFilter("ChoosingBot:Img"))
async def send_image(message: types.Message):
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
