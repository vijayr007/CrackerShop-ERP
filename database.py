import sqlite3
import logging

# Configure Logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Database:
    def __init__(self):
        # Using a consistent naming convention for the db file
        self.conn = sqlite3.connect("cracker_shop.db")
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.run_migrations() # Ensures existing DBs get new columns

    def create_tables(self):
        # 1. Inventory Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                product_code TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                price REAL,
                stock INTEGER,
                discount_percent REAL DEFAULT 0,
                sold_qty INTEGER DEFAULT 0
            )""")
        
        # 2. Sales Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id TEXT,
                item_name TEXT,
                category TEXT,
                quantity INTEGER,
                total REAL,
                discount_amount REAL DEFAULT 0,
                payment_mode TEXT,
                customer_phone TEXT,
                created_by TEXT,
                date TEXT
            )""")

        # 3. Customer CRM Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                phone TEXT PRIMARY KEY,
                name TEXT,
                address TEXT
            )""")
        
        # 4. Users Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE, 
                password TEXT, 
                role TEXT
            )""")
        
        # 5. Categories Table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cat_code TEXT UNIQUE,
                name TEXT,
                description TEXT
            )""")

        # Initial Data Seeds
        self.cursor.execute("INSERT OR IGNORE INTO categories (cat_code, name, description) VALUES ('GEN', 'General', 'Default Category')")
        self.cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        
        self.conn.commit()
        logging.info("Database tables initialized successfully.")

    def run_migrations(self):
        """Adds columns to existing tables if they don't exist."""
        # Check if sales table has the new columns we added recently
        self.cursor.execute("PRAGMA table_info(sales)")
        columns = [column[1] for column in self.cursor.fetchall()]
        
        migrations = {
            "discount_amount": "ALTER TABLE sales ADD COLUMN discount_amount REAL DEFAULT 0",
            "payment_mode": "ALTER TABLE sales ADD COLUMN payment_mode TEXT DEFAULT 'Cash'",
            "customer_phone": "ALTER TABLE sales ADD COLUMN customer_phone TEXT",
            "created_by": "ALTER TABLE sales ADD COLUMN created_by TEXT"
        }

        for col, sql in migrations.items():
            if col not in columns:
                try:
                    self.cursor.execute(sql)
                    self.conn.commit()
                    logging.info(f"Migration: Added column {col} to sales table.")
                except Exception as e:
                    logging.error(f"Migration failed for {col}: {e}")

# Create a single instance to be used across the app
db = Database()