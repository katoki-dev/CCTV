import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('database.db')

# Get all table names
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("=" * 60)
print("DATABASE SCHEMA - CEMSS SQLite Database")
print("=" * 60)
print(f"\nTables found: {len(tables)}\n")

for table in tables:
    table_name = table[0]
    print(f"\n📊 TABLE: {table_name}")
    print("-" * 60)
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print("Columns:")
    for col in columns:
        col_id, col_name, col_type, not_null, default, pk = col
        pk_marker = " [PRIMARY KEY]" if pk else ""
        null_marker = " NOT NULL" if not_null else ""
        print(f"  - {col_name}: {col_type}{pk_marker}{null_marker}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\nRow count: {count}")
    
    # Show sample data if table has rows
    if count > 0 and count <= 5:
        print(f"\nSample data (all {count} rows):")
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print(df.to_string(index=False))
    elif count > 0:
        print(f"\nSample data (first 3 rows):")
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
        print(df.to_string(index=False))

print("\n" + "=" * 60)
print("DATABASE EXPLORATION COMPLETE")
print("=" * 60)

conn.close()
