from database import Database
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_ID = os.getenv("ADMIN_ID")

def check_admin():
    if not ADMIN_ID:
        print("Ошибка: ADMIN_ID не установлен в .env файле")
        return False
    return True

def print_all_history():
    db = Database('bot_history.db')
    history = db.get_all_history()
    
    print("\n=== История всех сообщений ===")
    for user_id, username, message, response, timestamp, chat_id in history:
        print(f"\nПользователь: {username} (ID: {user_id})")
        print(f"Время: {timestamp}")
        print(f"Chat ID: {chat_id}")
        print(f"Сообщение: {message}")
        print(f"Ответ: {response}")
        print("-" * 50)

def print_user_history(user_id: int):
    db = Database('bot_history.db')
    history = db.get_user_history(user_id)
    
    print(f"\n=== История сообщений пользователя {user_id} ===")
    for message, response, timestamp, chat_id in history:
        print(f"\nВремя: {timestamp}")
        print(f"Chat ID: {chat_id}")
        print(f"Сообщение: {message}")
        print(f"Ответ: {response}")
        print("-" * 50)

if __name__ == "__main__":
    if not check_admin():
        print("Доступ запрещен. Установите ADMIN_ID в .env файле")
        exit(1)
        
    while True:
        print("\nВыберите действие:")
        print("1. Показать всю историю")
        print("2. Показать историю конкретного пользователя")
        print("3. Выход")
        
        choice = input("Ваш выбор: ")
        
        if choice == "1":
            print_all_history()
        elif choice == "2":
            user_id = int(input("Введите ID пользователя: "))
            print_user_history(user_id)
        elif choice == "3":
            break
        else:
            print("Неверный выбор") 