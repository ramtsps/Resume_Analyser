import sqlite3

# Create or connect to an SQLite3 database
conn = sqlite3.connect("db.sqlite3")  # This creates db.sqlite3 if it doesn't exist
cursor = conn.cursor()

# Create a sample table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
''')

# Commit changes and close connection
conn.commit()
conn.close()

print("Database and table created successfully!")
