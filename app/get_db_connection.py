import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')  # Шлях до вашої бази даних
    conn.row_factory = sqlite3.Row
    return conn
