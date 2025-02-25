from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Dict, Any, Callable, Awaitable

class CommandMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Список команд и кнопок, которые должны работать в любом состоянии
        priority_commands = ['/models', '🤖 Модели AI', '📜 История']
        
        # Если это приоритетная команда или кнопка
        if isinstance(event, Message) and event.text and event.text in priority_commands:
            # Временно сохраняем текущее состояние
            state = data.get('state')
            if state:
                current_state = await state.get_state()
                # Временно очищаем состояние для обработки команды
                await state.clear()
                # Обрабатываем команду
                result = await handler(event, data)
                # Если состояние не было изменено обработчиком, восстанавливаем его
                if await state.get_state() is None and current_state:
                    await state.set_state(current_state)
                return result
        
        # Для всех остальных сообщений используем стандартную обработку
        return await handler(event, data) 