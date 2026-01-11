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
        self.conn = sqlite3.connect("cracker_shop.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Inventory with Category
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE,
            name TEXT, 
            category TEXT, 
            price REAL, 
            stock INTEGER, 
            sold_qty INTEGER DEFAULT 0)''')
        
        # Sales with Category and Full Timestamp
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT, 
            item_name TEXT, 
            category TEXT,
            quantity INTEGER, 
            total REAL, 
            date TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, role TEXT)''')
        
        # Inside database.py create_tables method:

        # Category Meta Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cat_code TEXT UNIQUE,
            name TEXT,
            description TEXT)''')

        # Ensure initial categories exist
        self.cursor.execute("INSERT OR IGNORE INTO categories (cat_code, name, description) VALUES ('GEN', 'General', 'Default Category')")
        self.conn.commit()
                
        self.cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        self.conn.commit()

db = Database()