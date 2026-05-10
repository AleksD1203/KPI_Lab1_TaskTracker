import sys
import MySQLdb

if len(sys.argv) < 5:
    print("Usage: python3 migrate.py <host> <user> <password> <database>")
    sys.exit(1)

DB_HOST, DB_USER, DB_PASS, DB_NAME = sys.argv[1:5]

try:
    conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
    print("Database migration completed successfully.")
except Exception as e:
    print(f"Migration failed: {e}")
    sys.exit(1)