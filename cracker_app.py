import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. PERSISTENCE MODULE (Database Logic) ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("cracker_shop.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Inventory Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, category TEXT, price REAL, stock INTEGER)''')
        
        # Sales Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT, quantity INTEGER, total REAL, date TEXT)''')
        
        # User Management Table
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, role TEXT)''')
        
        # Create default Admin if not exists
        self.cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                           ('admin', 'admin123', 'Admin'))
        self.conn.commit()

db = Database()

# --- 2. MAIN APPLICATION UI ---
class CrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CrackerShop Pro v1.0")
        self.geometry("1100x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.current_user = None
        self.current_role = None
        self.show_login()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    # --- LOGIN MODULE ---
    def show_login(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self, width=350, height=400)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="Store Login", font=("Arial", 24, "bold")).pack(pady=30)
        
        self.user_entry = ctk.CTkEntry(frame, placeholder_text="Username", width=220)
        self.user_entry.pack(pady=10)
        
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=220)
        self.pass_entry.pack(pady=10)

        ctk.CTkButton(frame, text="Login", command=self.handle_login, width=220).pack(pady=25)

    def handle_login(self):
        u, p = self.user_entry.get(), self.pass_entry.get()
        db.cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
        res = db.cursor.fetchone()
        
        if res:
            self.current_user = u
            self.current_role = res[0]
            self.show_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid Credentials")

    # --- DASHBOARD & SIDEBAR ---
    def show_dashboard(self):
        self.clear_screen()
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="CRACKER SHOP", font=("Arial", 20, "bold")).pack(pady=20)
        ctk.CTkLabel(self.sidebar, text=f"User: {self.current_user}\nRole: {self.current_role}", font=("Arial", 12)).pack(pady=5)

        menu_items = [
            ("📦 Inventory", self.show_inventory),
            ("💳 Billing / POS", self.show_billing)
        ]

        if self.current_role == "Admin":
            menu_items.append(("👥 Users", self.show_users))
            menu_items.append(("📊 Reports", self.show_reports))

        for text, cmd in menu_items:
            ctk.CTkButton(self.sidebar, text=text, command=cmd, fg_color="transparent", anchor="w").pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(self.sidebar, text="Logout", command=self.show_login, fg_color="#d9534f").pack(side="bottom", fill="x", padx=10, pady=20)

        self.main_view = ctk.CTkFrame(self, corner_radius=15)
        self.main_view.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self.show_inventory()

    # --- INVENTORY MODULE (with CSV Upload) ---
# --- ENHANCED INVENTORY MODULE (Manual Entry + CSV) ---
    def show_inventory(self):
        self.clear_main_view()
        ctk.CTkLabel(self.main_view, text="Inventory Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        # 1. Manual Entry Form
        entry_frame = ctk.CTkFrame(self.main_view)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        self.inv_name = ctk.CTkEntry(entry_frame, placeholder_text="Item Name", width=150)
        self.inv_name.grid(row=0, column=0, padx=5, pady=10)
        
        self.inv_cat = ctk.CTkComboBox(entry_frame, values=["Sparklers", "Crackers", "Rockets", "Fountains"], width=130)
        self.inv_cat.grid(row=0, column=1, padx=5)
        
        self.inv_price = ctk.CTkEntry(entry_frame, placeholder_text="Price", width=80)
        self.inv_price.grid(row=0, column=2, padx=5)
        
        self.inv_stock = ctk.CTkEntry(entry_frame, placeholder_text="Stock", width=80)
        self.inv_stock.grid(row=0, column=3, padx=5)
        
        ctk.CTkButton(entry_frame, text="Add Item", fg_color="#2ecc71", command=self.add_to_inventory, width=100).grid(row=0, column=4, padx=5)
        ctk.CTkButton(entry_frame, text="Import CSV", command=self.upload_csv, width=100).grid(row=0, column=5, padx=5)

        # 2. Inventory Table
        self.tree = self.create_treeview(("ID", "Name", "Category", "Price", "Stock"))
        
        # 3. Action Buttons (Delete)
        action_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        action_frame.pack(fill="x", padx=20)
        ctk.CTkButton(action_frame, text="Delete Selected Item", fg_color="#e74c3c", command=self.delete_inventory_item).pack(side="right")

        self.refresh_inventory()

    def add_to_inventory(self):
        name = self.inv_name.get()
        cat = self.inv_cat.get()
        price = self.inv_price.get()
        stock = self.inv_stock.get()

        if name and price and stock:
            try:
                db.cursor.execute("INSERT INTO inventory (name, category, price, stock) VALUES (?, ?, ?, ?)",
                                 (name, cat, float(price), int(stock)))
                db.conn.commit()
                self.refresh_inventory()
                # Clear fields
                self.inv_name.delete(0, 'end')
                self.inv_price.delete(0, 'end')
                self.inv_stock.delete(0, 'end')
                messagebox.showinfo("Success", f"{name} added to inventory!")
            except ValueError:
                messagebox.showerror("Input Error", "Price and Stock must be numbers")
        else:
            messagebox.showerror("Error", "Please fill all fields")

    def delete_inventory_item(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item_id = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this item permanently?"):
            db.cursor.execute("DELETE FROM inventory WHERE id=?", (item_id,))
            db.conn.commit()
            self.refresh_inventory()

    # --- UPDATED BILLING (Delete from Cart) ---
    def show_billing(self):
        # ... [Keep previous show_billing code but add this button] ...
        # Add a "Remove Item" button below the cart table
        ctk.CTkButton(self.main_view, text="Remove Selected from Cart", 
                     fg_color="#e74c3c", command=self.remove_from_cart).pack(pady=5)

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        
        # Get index of selected item in the local list
        index = self.cart_tree.index(selected[0])
        del self.cart_items[index]
        self.update_cart_ui()

    def upload_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                df = pd.read_csv(path)
                for _, row in df.iterrows():
                    db.cursor.execute("INSERT INTO inventory (name, category, price, stock) VALUES (?, ?, ?, ?)",
                                     (row['name'], row['category'], row['price'], row['stock']))
                db.conn.commit()
                self.refresh_inventory()
                messagebox.showinfo("Success", "Stock imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse CSV: {e}")

    def refresh_inventory(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        db.cursor.execute("SELECT * FROM inventory")
        for row in db.cursor.fetchall(): self.tree.insert("", "end", values=row)

    # --- BILLING MODULE ---
# --- ENHANCED BILLING MODULE ---
# --- ENHANCED BILLING MODULE ---
    def show_billing(self):
        self.clear_main_view()
        self.cart_items = []  # Local list to hold current transaction data
        
        ctk.CTkLabel(self.main_view, text="Point of Sale | Billing", font=("Arial", 22, "bold")).pack(pady=10)

        # 1. Search & Add Section
        search_frame = ctk.CTkFrame(self.main_view)
        search_frame.pack(fill="x", padx=20, pady=10)

        self.search_input = ctk.CTkEntry(search_frame, placeholder_text="Enter Product Name...", width=250)
        self.search_input.grid(row=0, column=0, padx=10, pady=10)
        
        ctk.CTkButton(search_frame, text="Search", command=self.search_and_display, width=80).grid(row=0, column=1, padx=5)
        
        self.billing_qty = ctk.CTkEntry(search_frame, placeholder_text="Qty", width=70)
        self.billing_qty.grid(row=0, column=2, padx=10)
        
        ctk.CTkButton(search_frame, text="Add to Bill", fg_color="#2ecc71", command=self.add_to_cart).grid(row=0, column=3, padx=5)

        # 2. Cart Table (The current bill)
        self.cart_tree = self.create_treeview(("ID", "Product", "Price", "Qty", "Subtotal"))
        self.cart_tree.pack(fill="both", expand=True, padx=20, pady=10)

        # 3. Actions & Summary
        action_frame = ctk.CTkFrame(self.main_view)
        action_frame.pack(fill="x", padx=20, pady=10)

        self.total_display = ctk.CTkLabel(action_frame, text="Total: $0.00", font=("Arial", 20, "bold"))
        self.total_display.pack(side="left", padx=20)

        ctk.CTkButton(action_frame, text="Cancel Item", fg_color="#e74c3c", command=self.remove_from_cart).pack(side="right", padx=10)
        ctk.CTkButton(action_frame, text="Finalize & Print", fg_color="#1f538d", command=self.finalize_bill).pack(side="right", padx=10)

    # --- BILLING LOGIC ---
    def search_and_display(self):
        query = self.search_input.get()
        db.cursor.execute("SELECT name, price, stock FROM inventory WHERE name LIKE ?", (f'%{query}%',))
        res = db.cursor.fetchone()
        if res:
            messagebox.showinfo("Product Found", f"Item: {res[0]}\nPrice: ${res[1]}\nAvailable Stock: {res[2]}")
        else:
            messagebox.showwarning("Not Found", "Item not in inventory.")

    def add_to_cart(self):
        name = self.search_input.get()
        qty_str = self.billing_qty.get()

        if not qty_str.isdigit():
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return

        qty = int(qty_str)
        db.cursor.execute("SELECT id, name, price, stock FROM inventory WHERE name = ?", (name,))
        item = db.cursor.fetchone()

        if item:
            if item[3] >= qty:
                subtotal = item[2] * qty
                self.cart_items.append({"id": item[0], "name": item[1], "price": item[2], "qty": qty, "total": subtotal})
                self.refresh_cart_ui()
                self.billing_qty.delete(0, 'end')
            else:
                messagebox.showerror("Stock Error", f"Insufficient stock! Available: {item[3]}")
        else:
            messagebox.showerror("Error", "Item not found. Please search for a valid item.")

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Select an item in the cart to cancel.")
            return
        
        # Get index of selected item and remove from list
        idx = self.cart_tree.index(selected[0])
        del self.cart_items[idx]
        self.refresh_cart_ui()

    def refresh_cart_ui(self):
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        grand_total = 0
        for item in self.cart_items:
            self.cart_tree.insert("", "end", values=(item['id'], item['name'], item['price'], item['qty'], item['total']))
            grand_total += item['total']
        self.total_display.configure(text=f"Total: ${grand_total:.2f}")

    def finalize_bill(self):
        if not self.cart_items:
            messagebox.showwarning("Empty Cart", "No items to bill.")
            return

        if messagebox.askyesno("Confirm", "Complete transaction and print receipt?"):
            receipt_header = f"--- CRACKER SHOP RECEIPT ---\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            receipt_body = ""
            grand_total = 0

            for item in self.cart_items:
                # 1. Update Database (Persistence)
                db.cursor.execute("UPDATE inventory SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
                db.cursor.execute("INSERT INTO sales (item_name, quantity, total, date) VALUES (?, ?, ?, ?)",
                                 (item['name'], item['qty'], item['total'], datetime.now().strftime("%Y-%m-%d")))
                
                # 2. Build Receipt Text
                receipt_body += f"{item['name']} x{item['qty']} @ ${item['price']} = ${item['total']:.2f}\n"
                grand_total += item['total']

            db.conn.commit()
            receipt_footer = f"----------------------------\nGRAND TOTAL: ${grand_total:.2f}\nThank you for your purchase!"
            
            # Show receipt and reset
            print(receipt_header + receipt_body + receipt_footer)
            messagebox.showinfo("Receipt Printed", receipt_header + receipt_body + receipt_footer)
            self.show_billing()
            
    def search_item(self):
        query = self.search_entry.get()
        db.cursor.execute("SELECT name, price, stock FROM inventory WHERE name LIKE ?", (f'%{query}%',))
        item = db.cursor.fetchone()
        
        if item:
            messagebox.showinfo("Item Found", f"Product: {item[0]}\nPrice: ${item[1]}\nIn Stock: {item[2]}")
        else:
            messagebox.showerror("Not Found", "Item does not exist in inventory.")

    def add_to_cart(self):
        query = self.search_entry.get()
        qty_str = self.qty_entry.get()

        if not qty_str.isdigit():
            messagebox.showerror("Error", "Enter a valid quantity")
            return

        qty = int(qty_str)
        db.cursor.execute("SELECT id, name, price, stock FROM inventory WHERE name = ?", (query,))
        item = db.cursor.fetchone()

        if item:
            if item[3] >= qty:
                subtotal = item[2] * qty
                self.cart_items.append({'id': item[0], 'name': item[1], 'price': item[2], 'qty': qty, 'subtotal': subtotal})
                self.update_cart_ui()
            else:
                messagebox.showerror("Low Stock", f"Only {item[3]} units available.")
        else:
            messagebox.showerror("Error", "Select an item first.")

    def update_cart_ui(self):
        # Refresh the table
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        grand_total = 0
        for item in self.cart_items:
            self.cart_tree.insert("", "end", values=(item['id'], item['name'], item['price'], item['qty'], item['subtotal']))
            grand_total += item['subtotal']
        
        self.total_label.configure(text=f"Grand Total: ${grand_total:.2f}")

    def finalize_invoice(self):
        if not self.cart_items:
            return

        # 1. Update Inventory and Save Sales
        invoice_text = "--- CRACKER SHOP RECEIPT ---\n"
        invoice_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        invoice_text += "----------------------------\n"
        
        grand_total = 0
        for item in self.cart_items:
            # Deduct from Database
            db.cursor.execute("UPDATE inventory SET stock = stock - ? WHERE id = ?", (item['qty'], item['id']))
            # Log to Sales
            db.cursor.execute("INSERT INTO sales (item_name, quantity, total, date) VALUES (?, ?, ?, ?)",
                             (item['name'], item['qty'], item['subtotal'], datetime.now().strftime("%Y-%m-%d")))
            
            invoice_text += f"{item['name']} x{item['qty']} : ${item['subtotal']:.2f}\n"
            grand_total += item['subtotal']

        db.conn.commit()
        invoice_text += "----------------------------\n"
        invoice_text += f"GRAND TOTAL: ${grand_total:.2f}\n"
        invoice_text += "--- Thank You! ---\n"

        # 2. "Print" Simulation
        print(invoice_text) # Output to terminal
        messagebox.showinfo("Invoice Printed", invoice_text)
        
        # 3. Reset
        self.show_billing()

    def process_sale(self):
        name, qty = self.bill_item.get(), self.bill_qty.get()
        if not name or not qty.isdigit(): return

        db.cursor.execute("SELECT price, stock FROM inventory WHERE name=?", (name,))
        item = db.cursor.fetchone()
        
        if item and item[1] >= int(qty):
            total = item[0] * int(qty)
            db.cursor.execute("UPDATE inventory SET stock = stock - ? WHERE name=?", (qty, name))
            db.cursor.execute("INSERT INTO sales (item_name, quantity, total, date) VALUES (?, ?, ?, ?)",
                             (name, qty, total, datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.conn.commit()
            messagebox.showinfo("Invoice", f"Total: ${total:.2f}\nStock Updated.")
            self.bill_item.delete(0, 'end'); self.bill_qty.delete(0, 'end')
        else:
            messagebox.showerror("Error", "Stock Unavailable")

    # --- USER MANAGEMENT MODULE ---
    def show_users(self):
        self.clear_main_view()
        ctk.CTkLabel(self.main_view, text="System User Accounts", font=("Arial", 22, "bold")).pack(pady=10)
        
        u_frame = ctk.CTkFrame(self.main_view)
        u_frame.pack(fill="x", padx=20, pady=10)
        
        self.u_name = ctk.CTkEntry(u_frame, placeholder_text="Username")
        self.u_name.grid(row=0, column=0, padx=5, pady=5)
        self.u_pass = ctk.CTkEntry(u_frame, placeholder_text="Password", show="*")
        self.u_pass.grid(row=0, column=1, padx=5, pady=5)
        self.u_role = ctk.CTkComboBox(u_frame, values=["Admin", "Staff"])
        self.u_role.grid(row=0, column=2, padx=5, pady=5)
        
        ctk.CTkButton(u_frame, text="Add User", command=self.add_user).grid(row=0, column=3, padx=5)
        
        self.user_tree = self.create_treeview(("ID", "Username", "Role"))
        self.refresh_users()

    def add_user(self):
        u, p, r = self.u_name.get(), self.u_pass.get(), self.u_role.get()
        if u and p:
            db.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (u, p, r))
            db.conn.commit()
            self.refresh_users()

    def refresh_users(self):
        for i in self.user_tree.get_children(): self.user_tree.delete(i)
        db.cursor.execute("SELECT id, username, role FROM users")
        for row in db.cursor.fetchall(): self.user_tree.insert("", "end", values=row)

    # --- REPORTING MODULE ---
    def show_reports(self):
        self.clear_main_view()
        db.cursor.execute("SELECT SUM(total) FROM sales")
        total_rev = db.cursor.fetchone()[0] or 0
        
        ctk.CTkLabel(self.main_view, text="Business Performance", font=("Arial", 22, "bold")).pack(pady=10)
        ctk.CTkLabel(self.main_view, text=f"Gross Revenue: ${total_rev:.2f}", font=("Arial", 24), text_color="#2ecc71").pack(pady=10)
        
        self.rep_tree = self.create_treeview(("ID", "Item", "Qty", "Total", "Date"))
        db.cursor.execute("SELECT * FROM sales ORDER BY id DESC")
        for row in db.cursor.fetchall(): self.rep_tree.insert("", "end", values=row)

    # --- HELPER METHODS ---
    def clear_main_view(self):
        for widget in self.main_view.winfo_children(): widget.destroy()

    def create_treeview(self, columns):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map("Treeview", background=[('selected', '#1f538d')])
        
        tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns: tree.heading(col, text=col)
        tree.pack(fill="both", expand=True, padx=20, pady=20)
        return tree

if __name__ == "__main__":
    app = CrackerApp()
    app.mainloop()