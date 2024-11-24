from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import get_db_connection  # Припускаємо, що функція підключення до БД знаходиться тут
import sqlite3

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                       (username, email, hashed_password))
        conn.commit()
        return jsonify({"success": True, "message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username or email already exists"}), 400
    finally:
        conn.close()  # Закриваємо з'єднання з базою даних

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):  # Перевіряємо пароль
            session['user_id'] = user[0]  # Припускаємо, що перший стовпець - це ID
            return jsonify({"success": True, "message": "Login successful"})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
    finally:
        conn.close()  # Закриваємо з'єднання з базою даних
