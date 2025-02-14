import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cur = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            response TEXT,
            timestamp DATETIME,
            chat_id TEXT
        )
        """)
        self.conn.commit()
    
    def add_message(self, user_id: int, message: str, response: str, chat_id: str):
        self.cur.execute(
            "INSERT INTO chat_history (user_id, message, response, timestamp, chat_id) VALUES (?, ?, ?, ?, ?)",
            (user_id, message, response, datetime.now(), chat_id)
        )
        self.conn.commit()
    
    def get_chat_history(self, user_id: int, limit: int = 5) -> list:
        self.cur.execute(
            "SELECT message, response FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        return self.cur.fetchall()
    
    def get_all_history(self, limit: int = 50) -> list:
        self.cur.execute("""
            SELECT 
                user_id,
                message,
                response,
                timestamp,
                chat_id
            FROM chat_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        return self.cur.fetchall()
    
    def get_user_history(self, user_id: int, limit: int = 20) -> list:
        self.cur.execute("""
            SELECT 
                message,
                response,
                timestamp,
                chat_id
            FROM chat_history 
            WHERE user_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (user_id, limit))
        return self.cur.fetchall() 