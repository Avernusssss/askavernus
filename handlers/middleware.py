from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Dict, Any, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

class CommandMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Список команд и кнопок, которые должны работать в любом состоянии
        priority_commands = ['/models', '🤖 Модели AI', '📜 История']
        
        # Логируем входящее сообщение
        if isinstance(event, Message) and event.text:
            logger.info(f"Middleware received message: {event.text}")
            
            # Если это приоритетная команда или кнопка
            if event.text in priority_commands:
                logger.info(f"Priority command detected: {event.text}")
                
                # Временно сохраняем текущее состояние
                state = data.get('state')
                if state:
                    current_state = await state.get_state()
                    logger.info(f"Current state before handling: {current_state}")
                    
                    # Временно очищаем состояние для обработки команды
                    await state.clear()
                    logger.info("State cleared for priority command")
                    
                    # Обрабатываем команду
                    result = await handler(event, data)
                    
                    # Проверяем состояние после обработки
                    new_state = await state.get_state()
                    logger.info(f"State after handling: {new_state}")
                    
                    # Если состояние не было изменено обработчиком, восстанавливаем его
                    if new_state is None and current_state:
                        logger.info(f"Restoring previous state: {current_state}")
                        await state.set_state(current_state)
                    
                    return result
        
        # Для всех остальных сообщений используем стандартную обработку
        return await handler(event, data) 