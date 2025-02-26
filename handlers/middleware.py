from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Dict, Any, Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

class CommandMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, является ли сообщение командой (начинается с /)
        if event.text and event.text.startswith('/'):
            # Устанавливаем специальный флаг, чтобы обозначить это сообщение как команду
            data["is_command"] = True
            
            # Извлекаем имя команды без '/'
            command = event.text.split()[0][1:]
            data["command"] = command
            
            # Если у пользователя активен state, временно сбрасываем его для обработки команды
            if data.get("state") is not None:
                original_state = data["state"]
                data["original_state"] = original_state
                data["state"] = None
        
        # Продолжаем обработку сообщения
        result = await handler(event, data)
        
        # Восстанавливаем оригинальный state, если он был сохранен
        if "original_state" in data:
            data["state"] = data["original_state"]
            
        return result

    async def on_process_message(self, message: types.Message, data: Dict[str, Any]):
        # Список команд и кнопок, которые должны работать в любом состоянии
        priority_commands = ['/models', '🤖 Модели AI', '📜 История']
        
        # Логируем входящее сообщение
        if isinstance(message, types.Message) and message.text:
            logger.info(f"Middleware received message: {message.text}")
            
            # Если это приоритетная команда или кнопка
            if message.text in priority_commands:
                logger.info(f"Priority command detected: {message.text}")
                
                # Временно сохраняем текущее состояние
                state = data.get('state')
                if state:
                    current_state = await state.get_state()
                    logger.info(f"Current state before handling: {current_state}")
                    
                    # Временно очищаем состояние для обработки команды
                    await state.clear()
                    logger.info("State cleared for priority command")
                    
                    # Обрабатываем команду
                    result = await handler(message, data)
                    
                    # Проверяем состояние после обработки
                    new_state = await state.get_state()
                    logger.info(f"State after handling: {new_state}")
                    
                    # Если состояние не было изменено обработчиком, восстанавливаем его
                    if new_state is None and current_state:
                        logger.info(f"Restoring previous state: {current_state}")
                        await state.set_state(current_state)
                    
                    return result
        
        # Для всех остальных сообщений используем стандартную обработку
        return await handler(message, data) 