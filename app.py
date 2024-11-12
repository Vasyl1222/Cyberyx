from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
import logging
logging.basicConfig(level=logging.DEBUG)



app = Flask(__name__)
app.secret_key = 'my_secret_key'  #  секретний ключ для роботи з сесіями

# Підключення до бази даних
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Це дозволяє звертатися до полів по імені
    return conn

# Функція для отримання всіх продуктів
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE category = 'popular'")
    products = cursor.fetchall()
    conn.close()
    return products

# Головна сторінка з усіма продуктами
@app.route('/')
def index():
    products = get_products()
    return render_template('index.html', products=products)

# Додавання товару в кошик
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []  # Ініціалізація кошика, якщо його немає

    found = False
    for item in session['cart']:
        if item['product_id'] == product_id:
            item['quantity'] += 1  # Якщо товар є, збільшуємо кількість
            found = True
            break
    
    if not found:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        conn.close()

        if product:
            session['cart'].append({'product_id': product_id, 'quantity': 1})  # Додаємо новий товар до кошика

    session.modified = True  # Потрібно, щоб зміни зберігалися в сесії
    return redirect(url_for('index')) 

# Сторінка з усіма товарами з фільтрацією та сортуванням
@app.route('/all_products')
def all_products():
    category = request.args.get('category')
    sort_by = request.args.get('sort_by', default='name', type=str)
    sort_order = request.args.get('sort_order', default='asc', type=str)

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM products"
    params = []
    if category:
        query += " WHERE category = ?"
        params.append(category)

    if sort_by == 'price':
        if sort_order == 'asc':
            query += " ORDER BY CAST(price AS REAL) ASC"
        else:
            query += " ORDER BY CAST(price AS REAL) DESC"
    elif sort_by == 'name':
        if sort_order == 'asc':
            query += " ORDER BY name ASC"
        else:
            query += " ORDER BY name DESC"
    
    cursor.execute(query, tuple(params))
    products = cursor.fetchall()
    conn.close()

    return render_template('all_products.html', products=products)

@app.route('/update_quantity/<int:product_id>', methods=['POST'])
def update_quantity(product_id):
    quantity = request.form.get('quantity', type=int)
    if 'cart' in session:
        for item in session['cart']:
            if item['product_id'] == product_id:
                if quantity > 0:
                    item['quantity'] = quantity  # Оновлюємо кількість
                else:
                    session['cart'].remove(item)  # Видаляємо товар, якщо кількість 0
                break
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        # Проходимо по всіх товарах у кошику
        session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]  # Видаляємо товар
        session.modified = True  # Потрібно, щоб зміни зберігалися в сесії
    return redirect(url_for('cart'))  # Перенаправлення назад на сторінку кошика

# Сторінка кошика
@app.route('/cart')
def cart():
    cart_items = []
    total_price = 0

    if 'cart' in session:
        conn = get_db_connection()
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

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        # Отримуємо дані з форми
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Хешуємо пароль перед збереженням у базі даних
        hashed_password = generate_password_hash(password)

        # Підключення до бази даних і збереження користувача
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Вставка даних користувача в таблицю
            cursor.execute(''' 
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))

            conn.commit()  # Підтверджуємо зміни

            # Перенаправляємо на сторінку особистого кабінету після успішної реєстрації
            return redirect(url_for('profile'))

        except sqlite3.IntegrityError:  # Обробка помилок, якщо логін або email вже існують
            return "Цей логін або email вже використовується."

        finally:
            conn.close()

    return render_template('auth.html')  # Повертаємо форму реєстрації







@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            # Перевірка пароля за допомогою хешу
            if check_password_hash(user['password'], password):  
                session['email'] = email
                session['username'] = user['username']
                return redirect(url_for('profile'))
            else:
                return "Невірний логін або пароль!"
        else:
            return "Невірний логін або пароль!"

        conn.close()

    return render_template('auth.html')


@app.route('/order_form')
def order_form():
    # Логіка для сторінки оформлення замовлення
    cart_items = []
    total_price = 0

    if 'cart' in session:
        conn = get_db_connection()
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

    return render_template('order_form.html', cart_items=cart_items, total_price=total_price)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    name = request.form.get('name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    comments = request.form.get('comments')

    # Перевірка наявності товарів у кошику
    if 'cart' not in session or len(session['cart']) == 0:
        flash("Ваша корзина пуста. Додайте товари перед оформленням замовлення.")
        return redirect(url_for('cart'))

    # Логування вмісту кошика
    print("Товари в кошику:", session['cart'])  

    # Підключення до бази даних
    conn = get_db_connection()
    cursor = conn.cursor()

    # Додавання замовлення в таблицю orders
    cursor.execute('''
        INSERT INTO orders (name, phone, address, comments)
        VALUES (?, ?, ?, ?)
    ''', (name, phone, address, comments))

    order_id = cursor.lastrowid  # Отримуємо ID нового замовлення
    conn.commit()  # Зберігаємо зміни в базі даних

    # Додавання товарів з кошика в таблицю order_items
    for item in session['cart']:
        # Отримання детальної інформації про товар
        cursor.execute('SELECT name, price FROM products WHERE id = ?', (item['product_id'],))
        product = cursor.fetchone()

        if product:
            product_name = product['name']
            product_price = float(''.join(filter(str.isdigit, product['price']))) 
            quantity = item['quantity']
            total_price = product_price * quantity

            # Логування даних перед додаванням в таблицю
            print(f"Товар: {product_name}, ціна: {product_price}, кількість: {quantity}, загальна ціна: {total_price}")

            cursor.execute('''
                INSERT INTO order_items (order_id, product_name, product_price, quantity, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, product_name, product_price, quantity, total_price))
        else:
            print(f"Товар не знайдений для ID: {item['product_id']}")

    conn.commit()  # Зберігаємо зміни в базі даних
    conn.close()

    # Очищення кошика після оформлення замовлення
    session.pop('cart', None)

    flash("Ваше замовлення успішно оформлене.")
    return redirect(url_for('index'))



@app.route('/admin')
def admin_panel():
    conn = get_db_connection()

    # Користувачі
    users_query = '''
        SELECT 
            id, 
            username, 
            email, 
            password
        FROM 
            users;
    '''
    users = conn.execute(users_query).fetchall()

    # Замовлення
    orders_query = '''
        SELECT 
            id AS order_id, 
            phone, 
            name, 
            address, 
            comments, 
            created_at
        FROM 
            orders;
    '''
    orders = conn.execute(orders_query).fetchall()

    # Товари в замовленнях
    order_items_query = '''
        SELECT 
            id, 
            order_id, 
            product_name, 
            product_price, 
            quantity, 
            total_price, 
            created_at
        FROM 
            order_items;
    '''
    order_items = conn.execute(order_items_query).fetchall()

    # Закриваємо з'єднання
    conn.close()

    # Повертаємо всі дані на шаблон
    return render_template('admin.html', users=users, orders=orders, order_items=order_items)

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Очищення ідентифікатора користувача з сесії
    return redirect(url_for('index'))


@app.route('/register', methods=['POST'])
def register():
    # Отримуємо дані з JSON запиту
    data = request.get_json()
    print("Отримані дані:", data)  # Додаємо лог, щоб перевірити, що дані доходять

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone', '')  # Перевіримо, чи поле "phone" є необов’язковим

    # Перевірка наявності обов'язкових полів
    if not all([username, email, password]):
        return jsonify({'success': False, 'message': 'Всі обов\'язкові поля повинні бути заповнені'}), 400

    # Підключення до бази даних
    conn = get_db_connection()
    cursor = conn.cursor()

    # Перевірка, чи користувач з таким email вже існує
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return jsonify({'success': False, 'message': 'Користувач з таким email вже існує'}), 400

    # Додаємо нового користувача в таблицю users
    cursor.execute('''
        INSERT INTO users (username, email, password, phone)
        VALUES (?, ?, ?, ?)
    ''', (username, email, password, phone))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Реєстрація успішна'}), 201

# Форма входу

@app.route('/profile')
def profile():
    if 'email' not in session:
        return redirect(url_for('login'))  # Якщо користувач не авторизований, перенаправити на сторінку входу
    return render_template('profile.html', username=session['username'])

if __name__ == '__main__':
    app.run(debug=True)  