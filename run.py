# file: /run.py
from threading import Thread
from waitress import serve
from main import app, check_status


if __name__ == "__main__":
    background_task = Thread(target=check_status)
    background_task.start()
    serve(app, host='localhost', port=5000, threads=4)