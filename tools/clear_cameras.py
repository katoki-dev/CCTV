import sqlite3

# Connect to the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Delete all cameras
cursor.execute("DELETE FROM cameras")
conn.commit()

# Check count
cursor.execute("SELECT COUNT(*) FROM cameras")
count = cursor.fetchone()[0]

print(f"✓ All cameras cleared. Current camera count: {count}")

conn.close()
