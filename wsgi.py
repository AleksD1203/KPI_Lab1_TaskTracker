import sys

sys.argv = ['app.py', '127.0.0.1', 'app_user', '1203', 'task_db']

from app import app

if __name__ == "__main__":
    app.run()