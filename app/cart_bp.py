from flask import Blueprint, render_template, session, redirect, url_for
import sqlite3

cart_bp = Blueprint('cart', __name__)

# Маршрут для перегляду кошика
@cart_bp.route('/')
def cart():
    cart_items = []
    total_price = 0

    if 'cart' in session:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Оцінка всіх товарів у кошику
        for item in session['cart']:
            cursor.execute('SELECT id, name, price, image FROM products WHERE id = ?', (item['product_id'],))
            product = cursor.fetchone()
            if product:
                # Перетворення ціни на float
                price = float(''.join(filter(str.isdigit, product['price'])))

                # Додавання товару до списку кошика
                cart_items.append({
                    'product_id': item['product_id'],
                    'name': product['name'],
                    'price': price,
                    'quantity': item['quantity'],
                    'image': product['image']
                })

                # Оновлення загальної ціни
                total_price += price * item['quantity']

        conn.close()

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)
