# Функции для базы данных
import sqlite3
from datetime import datetime

import pandas as pd


def register_user(user_id, name, address):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, name, address) VALUES (?, ?, ?)",
                       (user_id, name, address))
        conn.commit()
    export_to_excel()


def create_order(user_id, quantity, address, phone, delivery_time):
    order_date = datetime.now().strftime('%d-%m-%Y %H:%M')
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, quantity, status, "
            "address, order_date, phone, "
            "delivery_time) VALUES (?, ?, 'Новый', ?, ?, ?, ?)",
            (user_id, quantity, address, order_date, phone, delivery_time))
        conn.commit()
        order_id = cursor.lastrowid
    export_to_excel()
    return order_id


def update_order_status(order_id, status):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        conn.commit()
    export_to_excel()


def get_user_id_by_order(order_id):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,))
        return cursor.fetchone()[0]


def get_nonconfirmed_orders():
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE status = 'Новый'")
        return cursor.fetchall()


def get_nondelivered_orders():
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE status = 'В пути'")
        return cursor.fetchall()


def get_nonsended_orders():
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE status = 'Оформлен'")
        return cursor.fetchall()


def get_order_details(order_id):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT order_id, user_id, quantity, "
            "status, address, order_date, phone, "
            "delivery_time FROM orders WHERE order_id = ?",
            (order_id,))
        return cursor.fetchone()


def update_user_phone(user_id, phone):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
        conn.commit()


def get_all_users():
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return cursor.fetchall()


def export_to_excel():
    with sqlite3.connect('water_base.db') as conn:
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        orders_df = pd.read_sql_query("SELECT * FROM orders", conn)
        reviews_df = pd.read_sql_query("SELECT * FROM reviews", conn)
    excel_file = 'water_data.xlsx'
    with pd.ExcelWriter('water_data.xlsx', engine='openpyxl') as writer:
        users_df.to_excel(writer, sheet_name='Users', index=False)
        orders_df.to_excel(writer, sheet_name='Orders', index=False)
        reviews_df.to_excel(writer, sheet_name='Reviews', index=False)
    return excel_file


def add_review(user_id, order_id, rating, comment):
    review_date = datetime.now().strftime('%d-%m-%Y %H:%M')
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reviews (user_id, order_id, rating, comment, review_date) VALUES (?, ?, ?, ?, ?)",
                       (user_id, order_id, rating, comment, review_date))
        conn.commit()
    export_to_excel()


def get_reviews_by_order(order_id):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rating, comment, review_date FROM reviews WHERE order_id = ?", (order_id,))
        return cursor.fetchall()


def get_delivered_orders():
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE status = 'Доставлен'")
        return cursor.fetchall()


def get_all_orders():
    conn = sqlite3.connect('water_base.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")  # Пример запроса, замените на свой
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_last_address(user_id):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT address FROM orders WHERE user_id = ? ORDER BY order_id DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def get_last_phone(user_id):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM orders WHERE user_id = ? ORDER BY order_id DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None


def save_admin_order(admin_id, order_id, message_id):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admin_order (admin_id, order_id, message_id) VALUES (?, ?, ?)",
                       (admin_id, order_id, message_id))


def get_admin_orders(order_id):
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT admin_id, message_id FROM admin_order WHERE order_id = ?", (order_id,))
