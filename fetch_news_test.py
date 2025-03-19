# fetch_news_test.py
import sqlite3
from datetime import datetime

def test_fetch():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    print("Creating news table...")
    cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       title TEXT, 
                       url TEXT UNIQUE, 
                       date TEXT, 
                       topic TEXT, 
                       source TEXT)''')
    
    # Insert dummy data
    dummy_data = [
        ("Test AI News", "https://example.com/ai", "2025-03-10T12:00:00Z", "artificial intelligence", "Test"),
        ("Test Blockchain News", "https://example.com/blockchain", "2025-03-10T12:01:00Z", "blockchain", "Test"),
    ]
    for title, url, date, topic, source in dummy_data:
        cursor.execute("INSERT OR IGNORE INTO news (title, url, date, topic, source) VALUES (?, ?, ?, ?, ?)", 
                      (title, url, date, topic, source))
    
    conn.commit()
    total_rows = cursor.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    print(f"Test data inserted at {datetime.now()}. Total rows: {total_rows}")
    conn.close()

if __name__ == "__main__":
    test_fetch()