import sqlite3


# создание базы данных
def setup_db():
    with sqlite3.connect('water_base.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                address TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quantity INTEGER,
                status TEXT,
                address TEXT,
                order_date TEXT,
                phone INT,
                delivery_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON orders(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON orders(status)')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id INTEGER,
                rating INTEGER,
                comment TEXT,
                review_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON reviews (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_id ON reviews (order_id)')
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admin_order (
                        admin_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        admin_id INTEGER,
                        order_id INTEGER,
                        message_id INTEGER,
                        FOREIGN KEY (admin_id) REFERENCES users (user_id),
                        FOREIGN KEY (order_id) REFERENCES orders (order_id)
                    )
                ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_order ON admin_order(admin_id, order_id)')
