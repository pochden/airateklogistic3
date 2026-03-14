from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import datetime
from pathlib import Path

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.secret_key = 'airatek_super_secret_2026'

DATA_DIR = Path('backend/data')

def load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Данные 
CITIES = ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Казань", "Краснодар"]

DISTANCES = {
    ("Москва", "Санкт-Петербург"): 700,
    ("Москва", "Екатеринбург"): 1400,
    ("Москва", "Новосибирск"): 3300,
    ("Москва", "Казань"): 800,
    ("Москва", "Краснодар"): 1200,
    ("Санкт-Петербург", "Екатеринбург"): 1900,
    ("Санкт-Петербург", "Новосибирск"): 4000,
    ("Санкт-Петербург", "Казань"): 1500,
    ("Санкт-Петербург", "Краснодар"): 1900,
    ("Екатеринбург", "Новосибирск"): 1900,
    ("Екатеринбург", "Казань"): 900,
    ("Екатеринбург", "Краснодар"): 2200,
    ("Новосибирск", "Казань"): 2500,
    ("Новосибирск", "Краснодар"): 3800,
    ("Казань", "Краснодар"): 1500,
}

# Обратные направления
for (a, b), dist in list(DISTANCES.items()):
    DISTANCES[(b, a)] = dist



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_json('users.json')
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']  
            session['role'] = user['role']
            return redirect('/cabinet')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = load_json('users.json')
        new_id = max([u['id'] for u in users], default=0) + 1
        
        users.append({
            "id": new_id,
            "username": request.form['username'],
            "password": request.form['password'],
            "role": "user",
            "email": request.form['email'],
            "full_name": "",
            "company": ""
        })
        save_json('users.json', users)
        return redirect('/login')
    return render_template('register.html')

@app.route('/cabinet', methods=['GET', 'POST'])
def cabinet():
    if 'user_id' not in session:
        return redirect('/login')
    users = load_json('users.json')
    orders = load_json('orders.json')
    user = next(u for u in users if u['id'] == session['user_id'])

    # ЕСЛИ АДМИН
    if user['role'] == 'admin':
        # изменение статуса заказа
        if request.method == 'POST':

            order_id = int(request.form['order_id'])
            new_status = request.form['status']

            for order in orders:
                if order['id'] == order_id:
                    order['status'] = new_status
                    break

            save_json('orders.json', orders)

            return redirect('/cabinet')

        return render_template(
            'admin_cabinet.html',
            user=user,
            orders=orders
        )

    # ЕСЛИ ОБЫЧНЫЙ ПОЛЬЗОВАТЕЛЬ
    if request.method == 'POST':

        user['email'] = request.form['email']
        user['full_name'] = request.form.get('full_name', '')
        user['company'] = request.form.get('company', '')
        save_json('users.json', users)
    user_orders = [o for o in orders if o['user_id'] == user['id']]

    return render_template(
        'user_cabinet.html',
        user=user,
        orders=user_orders
    )

@app.route('/order', methods=['GET', 'POST'])
def order():
    if 'user_id' not in session:
        return redirect('/login')
    
    tariffs = load_json('tariffs.json')
    
    if request.method == 'POST':
        from_city = request.form['from_city']
        to_city = request.form['to_city']
        weight = float(request.form['weight'])
        tariff_id = int(request.form['tariff'])
        
        dist = DISTANCES.get((from_city, to_city), 1000)
        tariff = next(t for t in tariffs if t['id'] == tariff_id)
        
        cost = round(dist * tariff['rate_per_km'] * (weight / 1000), 0)
        days = tariff['days']
        
        orders = load_json('orders.json')
        new_id = max([o.get('id', 0) for o in orders], default=0) + 1
        
        orders.append({
            "id": new_id,
            "user_id": session['user_id'],
            "from_city": from_city,
            "to_city": to_city,
            "weight": weight,
            "tariff": tariff['name'],
            "cost": cost,
            "delivery_days": days,
            "status_history": [{
                "date": datetime.date.today().isoformat(),
                "status": "Заказ принят",
                "location": f"{from_city}, склад отправления"
            }]
        })
        save_json('orders.json', orders)
        return redirect(f'/track/{new_id}')
    
    return render_template('order.html', tariffs=tariffs, cities=CITIES)

@app.route('/track/<int:order_id>')
def track(order_id):
    orders = load_json('orders.json')
    order = next((o for o in orders if o.get('id') == order_id), None)
    if not order:
        return "Заказ не найден", 404
    return render_template('track.html', order=order)

@app.route('/api/add_status', methods=['POST'])
def add_status():
    if session.get('role') != 'admin':
        return jsonify({"error": "Нет доступа"}), 403
    
    data = request.get_json()
    if not data or 'order_id' not in data:
        return jsonify({"error": "Нет данных"}), 400
    
    order_id = data['order_id']
    orders = load_json('orders.json')
    
    # DEBUG в терминале
    print(f"[DEBUG] Ищем заказ ID: {order_id} (тип {type(order_id)})")
    print(f"[DEBUG] Доступные ID в orders.json: {[o.get('id') for o in orders]}")
    print(f"[DEBUG] Типы ID: {[type(o.get('id')) for o in orders]}")
    
    # Сравнение такое работает даже при разных типах
    order = next((o for o in orders if str(o.get('id')) == str(order_id)), None)
    
    if order:
        order['status_history'].append({
            "date": datetime.date.today().isoformat(),
            "status": data['status'],
            "location": data['location']
        })
        save_json('orders.json', orders)
        print(f"[DEBUG] ✅ Статус успешно добавлен к заказу {order_id}")
        return jsonify({"success": True})
    
    print(f"[DEBUG] ❌ Заказ {order_id} НЕ найден!")
    return jsonify({"error": "Заказ не найден"}), 404

@app.route('/change_password', methods=['POST'])
def change_password():

    if 'user_id' not in session:
        return redirect('/login')

    users = load_json('users.json')

    user = next(u for u in users if u['id'] == session['user_id'])

    current = request.form['current_password']
    new = request.form['new_password']

    if user['password'] != current:
        return "Неверный текущий пароль"

    user['password'] = new

    save_json('users.json', users)

    return redirect('/cabinet')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == "__main__":
    app.run()   
