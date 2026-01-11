import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import time, logging

class BillingModule:
    def __init__(self, main_view, db, current_user):
        # Added current_user to track who is billing
        self.main_view = main_view
        self.db = db
        self.current_user = current_user
        self.cart = []

    def render(self):
        for w in self.main_view.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.main_view, text="Billing Terminal", font=("Arial", 22, "bold")).pack(pady=5)
        
        # --- Customer Details Frame ---
        c_frame = ctk.CTkFrame(self.main_view)
        c_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(c_frame, text="Customer Info:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=5)
        
        self.c_phone = ctk.CTkEntry(c_frame, placeholder_text="Phone Number", width=150)
        self.c_phone.grid(row=0, column=1, padx=5, pady=5)
        self.c_phone.bind("<KeyRelease>", lambda e: self.lookup_customer())

        self.c_name = ctk.CTkEntry(c_frame, placeholder_text="Customer Name", width=150)
        self.c_name.grid(row=0, column=2, padx=5, pady=5)

        self.c_address = ctk.CTkEntry(c_frame, placeholder_text="Shipping Address", width=350)
        self.c_address.grid(row=0, column=3, padx=5, pady=5)

        # --- Search & Filter Frame ---
        f = ctk.CTkFrame(self.main_view)
        f.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(f, text="Category:").grid(row=0, column=0, padx=5)
        self.db.cursor.execute("SELECT name FROM categories")
        cats = ["All Categories"] + [r[0] for r in self.db.cursor.fetchall()]
        self.cat_filter = ctk.CTkComboBox(f, values=cats, width=140, command=lambda x: self.handle_search())
        self.cat_filter.set("All Categories")
        self.cat_filter.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(f, text="Search:").grid(row=0, column=2, padx=5)
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(f, textvariable=self.search_var, placeholder_text="Name...", width=150)
        self.search_entry.grid(row=0, column=3, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.handle_search())

        self.res_dropdown = ctk.CTkComboBox(f, values=[], width=280)
        self.res_dropdown.grid(row=0, column=4, padx=5)

        self.qty = ctk.CTkEntry(f, placeholder_text="Qty", width=60)
        self.qty.insert(0, "1")
        self.qty.grid(row=0, column=5, padx=5)
        
        ctk.CTkButton(f, text="Add", width=80, command=self.add_to_cart).grid(row=0, column=6, padx=10)

        # --- Cart Table ---
        cols = ("Code", "Item Name", "Category", "Price", "Qty", "Total")
        self.tree = ttk.Treeview(self.main_view, columns=cols, show='headings')
        for c in cols: 
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Footer ---
        footer = ctk.CTkFrame(self.main_view, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=10)
        
        # Display who is billing
        ctk.CTkLabel(footer, text=f"Billed By: {self.current_user}", font=("Arial", 12, "italic")).pack(side="left")

        self.total_lbl = ctk.CTkLabel(footer, text="Grand Total: ₹0.00", font=("Arial", 20, "bold"), text_color="#2ecc71")
        self.total_lbl.pack(side="right", padx=20)
        
        ctk.CTkButton(footer, text="Complete Sale", fg_color="#27ae60", command=self.checkout).pack(side="right", padx=20)

        self.handle_search()

    def lookup_customer(self):
        """Auto-fills name and address if phone exists in DB."""
        phone = self.c_phone.get().strip()
        if len(phone) >= 10:
            self.db.cursor.execute("SELECT name, address FROM customers WHERE phone=?", (phone,))
            res = self.db.cursor.fetchone()
            if res:
                self.c_name.delete(0, 'end')
                self.c_name.insert(0, res[0])
                self.c_address.delete(0, 'end')
                self.c_address.insert(0, res[1])

    def get_cart_qty(self, product_name):
        return sum(item[4] for item in self.cart if item[1] == product_name)

    def handle_search(self):
        val = self.search_var.get()
        cat = self.cat_filter.get()
        query = "SELECT name, stock FROM inventory WHERE (name LIKE ? OR product_code LIKE ?)"
        params = [f"%{val}%", f"%{val}%"]
        if cat != "All Categories":
            query += " AND category = ?"
            params.append(cat)
        query += " ORDER BY name ASC LIMIT 50"
        self.db.cursor.execute(query, params)
        db_results = self.db.cursor.fetchall()
        formatted_results = [f"{n} (Avail: {s - self.get_cart_qty(n)})" for n, s in db_results]
        self.res_dropdown.configure(values=formatted_results)
        if formatted_results: self.res_dropdown.set(formatted_results[0])

    def add_to_cart(self):
        selected_raw = self.res_dropdown.get()
        if "No results found" in selected_raw or not selected_raw: return
        selected_name = selected_raw.split(" (Avail:")[0]
        try:
            qty_to_add = int(self.qty.get())
            if qty_to_add <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Enter a valid quantity")
            return

        self.db.cursor.execute("SELECT product_code, name, category, price, stock FROM inventory WHERE name=?", (selected_name,))
        res = self.db.cursor.fetchone()
        if res:
            p_code, p_name, p_cat, p_price, p_db_stock = res
            current_in_cart = self.get_cart_qty(p_name)
            if (current_in_cart + qty_to_add) > p_db_stock:
                messagebox.showerror("Stock Error", "Insufficient Stock!")
                return
            
            found = False
            for item in self.cart:
                if item[0] == p_code:
                    item[4] += qty_to_add
                    item[5] = item[3] * item[4]
                    found = True
                    break
            if not found:
                self.cart.append([p_code, p_name, p_cat, p_price, qty_to_add, p_price * qty_to_add])

            self.refresh_table()
            self.update_total()
            self.handle_search() 

    def refresh_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for item in self.cart: self.tree.insert("", "end", values=item)

    def update_total(self):
        total = sum(i[5] for i in self.cart)
        self.total_lbl.configure(text=f"Grand Total: ₹{total:.2f}")

    def checkout(self):
        if not self.cart: return
        phone = self.c_phone.get().strip()
        name = self.c_name.get().strip()
        addr = self.c_address.get().strip()
        
        bill_id = f"BILL-{int(time.time())}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # 1. Update/Save Customer CRM
            if phone and name:
                self.db.cursor.execute("""
                    INSERT INTO customers (phone, name, address) VALUES (?,?,?)
                    ON CONFLICT(phone) DO UPDATE SET name=excluded.name, address=excluded.address
                """, (phone, name, addr))

            # 2. Process Transactions
            for item in self.cart:
                p_code, p_name, p_cat, p_price, p_qty, p_total = item
                # Update Stock
                self.db.cursor.execute("UPDATE inventory SET stock=stock-?, sold_qty=sold_qty+? WHERE product_code=?", (p_qty, p_qty, p_code))
                # Insert Sale Record with Customer and User Info
                self.db.cursor.execute("""
                    INSERT INTO sales (bill_id, item_name, category, quantity, total, customer_phone, created_by, date) 
                    VALUES (?,?,?,?,?,?,?,?)
                """, (bill_id, p_name, p_cat, p_qty, p_total, phone, self.current_user, now))

            self.db.conn.commit()
            messagebox.showinfo("Success", f"Bill {bill_id} Saved!\nBilled by: {self.current_user}")
            self.cart = []
            self.render()
        except Exception as e:
            logging.error(f"CHECKOUT ERROR: {str(e)}")
            messagebox.showerror("Error", f"Checkout failed: {e}")