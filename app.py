from flask import Flask, render_template, request, redirect, url_for, flash
from database.requests import get_nonconfirmed_orders, get_nondelivered_orders, get_delivered_orders, \
    update_order_status

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Используется для сессий и флеш-сообщений, замените на свой ключ


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/orders')
def orders():
    nonconfirmed_orders = get_nonconfirmed_orders()
    nondelivered_orders = get_nondelivered_orders()
    delivered_orders = get_delivered_orders()
    return render_template('orders.html', nonconfirmed_orders=nonconfirmed_orders,
                           nondelivered_orders=nondelivered_orders, delivered_orders=delivered_orders)


@app.route('/update_status', methods=['POST'])
def update_status():
    order_id = request.form['order_id']
    new_status = request.form['new_status']
    update_order_status(order_id, new_status)
    flash(f'Status of order {order_id} updated to {new_status}')
    return redirect(url_for('orders'))


if __name__ == '__main__':
    app.run(debug=True)
