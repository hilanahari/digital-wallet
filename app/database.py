import sqlite3

DB_PATH = "wallet.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)  # מתחבר לקובץ, ויוצר אותו אם הוא לא קיים
    conn.row_factory = sqlite3.Row  # שלא יוחזר  כ- tuple
    conn.execute("PRAGMA foreign_keys = ON") # מוודאת שהקשרים שאנו יוצרים בין טבלאות נאכפים בזמן אמת 
    
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts(
 	        id INTEGER PRIMARY KEY,
            owner TEXT NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
            user_id INTEGER 
            )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions(
 	        id INTEGER PRIMARY KEY,
 	        account_id INTEGER NOT NULL REFERENCES accounts(id),
 	        counterparty_id INTEGER REFERENCES accounts(id),
 	        type TEXT NOT NULL CHECK (type IN ('deposit', 'transfer_in' , 'transfer_out')), 
 	        amount INTEGER NOT NULL CHECK (amount != 0),
 	        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
    """)
    conn.commit()  # שומר את השינויים בקובץ בפועל
    conn.close()  # סוגר את החיבור
