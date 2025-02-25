import time
from mnnai import MNN
from functools import lru_cache
from cachetools import TTLCache

class AIService:
    def __init__(self, api_key, default_model="gpt-4o-mini"):
        self.client = MNN(
            key=api_key,
            max_retries=2,
            timeout=60,
            debug=False
        )
        self.current_model = default_model
        self.models_cache = TTLCache(maxsize=100, ttl=300)  # Кэш на 5 минут
    
    async def get_available_models(self):
        """Получает список доступных моделей с кэшированием"""
        if 'models' not in self.models_cache:
            try:
                models = self.client.GetModels()
                if models:
                    self.models_cache['models'] = models
            except Exception as e:
                print(f"Error getting models: {e}")
                # Если кэш пуст и произошла ошибка, добавляем модели по умолчанию
                if 'models' not in self.models_cache:
                    self.models_cache['models'] = ["gpt-4o-mini", "gpt-4o", "dall-e-3"]
        
        return self.models_cache.get('models', [])
    
    async def get_image_models(self):
        """Получает список моделей, поддерживающих генерацию изображений"""
        try:
            models = await self.get_available_models()
            return [model for model in models if 'dall-e' in model.lower()]
        except Exception as e:
            print(f"Error getting image models: {e}")
            return ["dall-e-3"]  # Возвращаем модель по умолчанию в случае ошибки
    
    async def chat_completion(self, messages, stream=True):
        """Выполняет запрос к модели чата"""
        try:
            return await self.client.chat.async_create(
                model=self.current_model,
                messages=messages,
                stream=stream
            )
        except Exception as e:
            print(f"Error in chat completion: {e}")
            raise
    
    async def generate_image(self, prompt):
        """Генерирует изображение по запросу"""
        try:
            # Для изображений используем модель DALL-E, если текущая модель не подходит
            img_models = await self.get_image_models()
            img_model = self.current_model if self.current_model in img_models else img_models[0]
            
            return await self.client.images.async_create(
                prompt=prompt,
                model=img_model,
                n=1,
                size="1024x1024"
            )
        except Exception as e:
            print(f"Error in image generation: {e}")
            raise
    
    def set_current_model(self, model_name):
        """Устанавливает текущую модель"""
        self.current_model = model_name
        return self.current_model
    
    def get_current_model(self):
        """Возвращает текущую модель"""
        return self.current_model 