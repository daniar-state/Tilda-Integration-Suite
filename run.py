# file: /run.py
from waitress import serve
from main import app


if __name__ == "__main__":
    serve(app, host='localhost', port=5000, threads=4)