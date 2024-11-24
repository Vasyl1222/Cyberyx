# app/cart_bp.py
from flask import Blueprint, session, redirect, url_for, request
from app import get_db_connection  # Замість app можна використовувати правильний шлях до get_db_connection

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form['quantity'])  # Отримуємо кількість товару
    conn = get_db_connection()
    cursor = conn.cursor()
    product = cursor.execute('SELECT id, name, price, image FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    if product:
        # Якщо товар є, додаємо до кошика в сесії
        if 'cart' not in session:
            session['cart'] = []

        cart_item = next((item for item in session['cart'] if item['product_id'] == product_id), None)

        if cart_item:
            cart_item['quantity'] += quantity  # Оновлюємо кількість
        else:
            session['cart'].append({
                'product_id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'image': product['image']
            })

        session.modified = True  # Зміни в сесії

    return redirect(url_for('cart.cart'))  # Вказуємо, що маршрут для картки знаходиться у картці
