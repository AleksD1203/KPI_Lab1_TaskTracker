import sys
from flask import Flask, jsonify, request
import MySQLdb

app = Flask(__name__)

if len(sys.argv) < 5:
    print("Usage: python3 app.py <host> <user> <password> <database>")
    sys.exit(1)

DB_HOST = sys.argv[1]
DB_USER = sys.argv[2]
DB_PASS = sys.argv[3]
DB_NAME = sys.argv[4]

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)

# 1. Головна сторінка
@app.route('/', methods=['GET'])
def index():
    html = """
    <html><body>
    <h1>Task Tracker API</h1>
    <ul>
        <li><a href="/health/alive">/health/alive</a></li>
        <li><a href="/health/ready">/health/ready</a></li>
        <li><a href="/tasks">/tasks</a></li>
    </ul>
    </body></html>
    """
    return html, 200

# 2. Ендпоінти
@app.route('/health/alive', methods=['GET'])
def alive():
    return "OK", 200

@app.route('/health/ready', methods=['GET'])
def ready():
    try:
        conn = get_db_connection()
        conn.close()
        return "OK", 200
    except Exception as e:
        return f"Database error: {str(e)}", 500

# 3. Отримання задач (HTML або JSON)
@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, title, status, created_at FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    
    if 'text/html' in request.headers.get('Accept', ''):
        html = "<html><body><h2>Task List</h2><table border='1'><tr><th>ID</th><th>Title</th><th>Status</th><th>Date</th></tr>"
        for t in tasks:
            html += f"<tr><td>{t['id']}</td><td>{t['title']}</td><td>{t['status']}</td><td>{t['created_at']}</td></tr>"
        html += "</table></body></html>"
        return html, 200
    
    return jsonify(tasks), 200

# 4. Створення задачі
@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Title is required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title) VALUES (%s)", (data['title'],))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task created successfully"}), 201

# 5. Зміна статусу задачі на "виконано"
@app.route('/tasks/<int:task_id>/done', methods=['POST'])
def complete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status='done' WHERE id=%s", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task marked as done"}), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)