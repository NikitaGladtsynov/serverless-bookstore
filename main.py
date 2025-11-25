from flask import Flask, request, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)

# Получаем URL базы из переменных окружения (Render передаёт его автоматически)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise Exception("DATABASE_URL не задан — база недоступна")
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages(
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("Таблица messages успешно создана/проверена")

# --------------------- Эндпоинты ---------------------

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
    # Сначала проверяем, есть ли база
    if not DATABASE_URL:
        return jsonify({"error": "База данных не подключена"}), 503

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

# --------------------- Безопасный запуск ---------------------

# Пытаемся инициализировать БД только если DATABASE_URL задан
if DATABASE_URL and DATABASE_URL.strip():
    try:
        init_db()
    except Exception as e:
        print(f"Не удалось подключиться к базе (это нормально, если база ещё не создана): {e}")
else:
    print("DATABASE_URL не задан — работаем без базы данных (Задания 1 и 2 доступны)")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)