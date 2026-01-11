import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("cracker_shop.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Inventory Table with Tracking
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE,
            name TEXT, category TEXT, price REAL, stock INTEGER, sold_qty INTEGER DEFAULT 0)''')
        
        # Sales Table with Bill ID
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT, item_name TEXT, quantity INTEGER, total REAL, date TEXT)''')
        
        # User Table for RBAC
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, role TEXT)''')
        
        # Default Admin Account
        self.cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        self.conn.commit()

db = Database()