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
            username TEXT,
            message TEXT,
            response TEXT,
            timestamp DATETIME,
            chat_id TEXT
        )
        """)
        
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS muted_users (
            user_id INTEGER PRIMARY KEY,
            muted_until DATETIME
        )
        """)
        self.conn.commit()
    
    def add_message(self, user_id: int, username: str, message: str, response: str, chat_id: str):
        self.cur.execute(
            "INSERT INTO chat_history (user_id, username, message, response, timestamp, chat_id) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, message, response, datetime.now(), chat_id)
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
                username,
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
    
    def add_mute(self, user_id: int, duration_seconds: int):
        self.cur.execute(
            "INSERT OR REPLACE INTO muted_users (user_id, muted_until) VALUES (?, datetime('now', '+' || ? || ' seconds'))",
            (user_id, duration_seconds)
        )
        self.conn.commit()
    
    def is_muted(self, user_id: int) -> bool:
        self.cur.execute(
            "SELECT 1 FROM muted_users WHERE user_id = ? AND muted_until > datetime('now')",
            (user_id,)
        )
        return bool(self.cur.fetchone()) 