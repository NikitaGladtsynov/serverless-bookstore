from flask import Flask, request, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)

# Подключение к БД (Render передаёт через переменную окружения)
DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# Инициализация таблицы при первом запуске
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
                CREATE TABLE IF NOT EXISTS messages
                (
                    id
                    SERIAL
                    PRIMARY
                    KEY,
                    name
                    TEXT
                    NOT
                    NULL,
                    message
                    TEXT
                    NOT
                    NULL,
                    created_at
                    TIMESTAMP
                    DEFAULT
                    CURRENT_TIMESTAMP
                )
                ''')
    conn.commit()
    cur.close()
    conn.close()


init_db()


@app.route('/')
def hello():
    return "Hello, Serverless! Это работает на Render.com без сервера и без карты ✅", 200


@app.route('/json', methods=['POST'])
def process_json():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Поле 'name' обязательно"}), 400

    name = data['name']
    response = {
        "message": f"Привет, {name}!",
        "length": len(name),
        "upper": name.upper(),
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), 200


@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'GET':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, message, created_at FROM messages ORDER BY created_at DESC')
        rows = cur.fetchall()
        cur.close()
        conn.close()

        result = [
            {"id": r[0], "name": r[1], "message": r[2], "created_at": r[3].isoformat()}
            for r in rows
        ]
        return jsonify(result), 200

    if request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data or 'message' not in data:
            return jsonify({"error": "Нужны поля 'name' и 'message'"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO messages (name, message) VALUES (%s, %s) RETURNING id',
            (data['name'], data['message'])
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "id": new_id}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)