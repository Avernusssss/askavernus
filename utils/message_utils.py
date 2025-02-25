from io import BytesIO
from aiogram import types

async def send_long_message(message: types.Message, text: str):
    """Отправляет длинное сообщение, разбивая его на части"""
    MAX_MESSAGE_LENGTH = 4000
    
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        part = text[i:i + MAX_MESSAGE_LENGTH]
        await message.answer(part)

async def send_as_file(message: types.Message, text: str, filename="response.txt"):
    """Отправляет длинный текст как файл"""
    bio = BytesIO(text.encode('utf-8'))
    bio.name = filename
    
    await message.answer_document(bio)

async def stream_response(message, stream, max_length=4000):
    """Оптимизированная функция для стриминга ответов"""
    full_response = ""
    current_part = ""
    msg = await message.answer("Думаю...")
    message_parts = []
    
    async for chunk in stream:
        if not chunk.choices[0].delta.content:
            continue
            
        content = chunk.choices[0].delta.content
        full_response += content
        current_part += content
        
        # Обновляем сообщение реже для снижения нагрузки на API Telegram
        if len(current_part) % 100 == 0:  # Обновляем каждые 100 символов вместо 20
            try:
                await msg.edit_text(current_part, parse_mode='Markdown')
            except:
                await msg.edit_text(current_part)
        
        # Создаем новое сообщение при достижении лимита
        if len(current_part) >= max_length:
            try:
                await msg.edit_text(current_part, parse_mode='Markdown')
            except:
                await msg.edit_text(current_part)
                
            message_parts.append(current_part)
            msg = await message.answer("Продолжение...")
            current_part = ""
    
    # Отправляем последнюю часть
    if current_part:
        try:
            await msg.edit_text(current_part, parse_mode='Markdown')
        except:
            await msg.edit_text(current_part)
        message_parts.append(current_part)
    
    return full_response, message_parts 