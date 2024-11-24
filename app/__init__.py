# app/__init__.py
from flask import Flask
from .cart_bp import cart_bp  # Імпортуємо Blueprint для кошика

def create_app():
    app = Flask(__name__)
    app.secret_key = 'my_secret_key'  # Для роботи з сесіями

    # Реєструємо Blueprint для кошика
    app.register_blueprint(cart_bp, url_prefix='/cart')

    return app
