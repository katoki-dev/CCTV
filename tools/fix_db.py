import sqlite3
import os

db_path = 'database.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_column(table, column, type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        print(f"Added column {column} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"Column {column} already exists in {table}")
        else:
            print(f"Error adding {column} to {table}: {e}")

# Fix Magazine table
add_column('magazines', 'description', 'VARCHAR(500)')
add_column('magazines', 'image_url', 'VARCHAR(255)')
add_column('magazines', 'content_image_url', 'VARCHAR(255)')

# Fix Events table (just in case)
add_column('events', 'camera_id', 'INTEGER')
add_column('events', 'is_live', 'BOOLEAN DEFAULT 0')
add_column('events', 'image_url', 'VARCHAR(255)')

conn.commit()
conn.close()
print("Database schema updated.")
