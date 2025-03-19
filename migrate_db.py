# migrate_db.py
import sqlite3

# Connect to the database
conn = sqlite3.connect('/Users/yashmandaviya/Newsfetcher/NewsFetcher/news.db')
cursor = conn.cursor()

# Create table if it doesn’t exist
cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   title TEXT, 
                   url TEXT UNIQUE, 
                   date TEXT, 
                   topic TEXT, 
                   source TEXT)''')
print("Ensured 'news' table exists or was created.")

# Check existing columns
cursor.execute("PRAGMA table_info(news)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Current columns: {columns}")

# Add 'language' column if missing
if 'language' not in columns:
    print("Adding 'language' column to news table...")
    cursor.execute("ALTER TABLE news ADD COLUMN language TEXT DEFAULT 'en'")
    print("Column 'language' added successfully.")
else:
    print("'language' column already exists.")

# Add 'rating' column if missing
if 'rating' not in columns:
    print("Adding 'rating' column to news table...")
    cursor.execute("ALTER TABLE news ADD COLUMN rating REAL DEFAULT 0.0")
    print("Column 'rating' added successfully.")
else:
    print("'rating' column already exists.")

# Verify the updated schema
cursor.execute("PRAGMA table_info(news)")
updated_columns = [col[1] for col in cursor.fetchall()]
print(f"Updated columns: {updated_columns}")

# Commit changes and close
conn.commit()
conn.close()
print("Database migration complete.")