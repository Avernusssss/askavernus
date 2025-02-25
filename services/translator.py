from googletrans import Translator

async def translate_text(data: str, src='ru', dest='en'):
    """Переводит текст с одного языка на другой"""
    try:
        async with Translator() as translator:
            result = await translator.translate(data, dest=dest, src=src)
            return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        # В случае ошибки возвращаем исходный текст
        return data 