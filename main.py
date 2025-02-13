from g4f import AsyncClient
from googletrans import Translator

import logging
import asyncio

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)

bot = Bot("7676133140:AAFQUfgJYcg7103J72adVTGJiJZ1m_-bAoQ")
dp = Dispatcher()
router = Router()


class ChoosingBot(StatesGroup):
    Gpt = State()
    Img = State()


@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.answer(
        "Здарова\n/gpt\n/img")


@dp.message(Command('gpt'))
async def set_state_gpt(message: types.Message, state: FSMContext):
    await message.answer("Ну спрашивай, я книжки читал.")
    await state.set_state(ChoosingBot.Gpt)


@dp.message(Command('img'))
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
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_input}],
            web_search=False

        )

        await msg.edit_text(response.choices[0].message.content, parse_mode='Markdown')

    except Exception as e:
        print("Error: ", e)
        chat_gpt_response = "Ну и хуйню ты сморозил..."

    # await msg.edit_text(chat_gpt_response, parse_mode='Markdown')


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


# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
