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
        
        # Предустановленный список моделей
        self.default_models = [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo",
            "claude-3-haiku",
            "claude-3-sonnet",
            "claude-3-opus",
            "dall-e-3"
        ]
    
    async def get_available_models(self):
        """Получает список доступных моделей с кэшированием"""
        if 'models' not in self.models_cache:
            try:
                # Пытаемся получить модели через API
                try:
                    models = self.client.GetModels()
                    if models and isinstance(models, list) and len(models) > 0:
                        self.models_cache['models'] = models
                    else:
                        # Если API вернул пустой список или не список, используем предустановленные модели
                        self.models_cache['models'] = self.default_models
                except (AttributeError, Exception) as e:
                    print(f"Error getting models from API: {e}")
                    # Если метод GetModels не существует или вызвал ошибку, используем предустановленные модели
                    self.models_cache['models'] = self.default_models
            except Exception as e:
                print(f"Unexpected error getting models: {e}")
                # В случае любой другой ошибки используем предустановленные модели
                self.models_cache['models'] = self.default_models
        
        return self.models_cache.get('models', self.default_models)
    
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