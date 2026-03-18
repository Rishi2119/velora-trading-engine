import sqlite3

try:
    conn = sqlite3.connect('d:/trading_engins/velora.db')
    cursor = conn.cursor()
    
    def add_column(table, column, type_def):
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
            print(f"Added {column}")
        except sqlite3.OperationalError as e:
            print(f"{column} - {e}")

    add_column('users', 'last_login', 'DATETIME')
    add_column('users', 'provider', 'VARCHAR(50) DEFAULT "local"')
    add_column('users', 'updated_at', 'DATETIME')

    conn.commit()
    conn.close()
    print("Database patch complete.")
except Exception as e:
    print(f"Error: {e}")
