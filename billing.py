import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import time, logging

class BillingModule:
    def __init__(self, main_view, db):
        self.main_view, self.db, self.cart = main_view, db, []

    def render(self):
        for w in self.main_view.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.main_view, text="Billing Terminal", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Search & Filter Frame ---
        f = ctk.CTkFrame(self.main_view)
        f.pack(fill="x", padx=20, pady=10)
        
        # 1. Category Filter
        ctk.CTkLabel(f, text="Category:").grid(row=0, column=0, padx=5)
        self.db.cursor.execute("SELECT name FROM categories")
        cats = ["All Categories"] + [r[0] for r in self.db.cursor.fetchall()]
        self.cat_filter = ctk.CTkComboBox(f, values=cats, width=140, command=lambda x: self.handle_search())
        self.cat_filter.set("All Categories")
        self.cat_filter.grid(row=0, column=1, padx=5)

        # 2. Dynamic Search Input
        ctk.CTkLabel(f, text="Search:").grid(row=0, column=2, padx=5)
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(f, textvariable=self.search_var, placeholder_text="Name...", width=150)
        self.search_entry.grid(row=0, column=3, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.handle_search())

        # 3. Dynamic Results Dropdown
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
        
        self.total_lbl = ctk.CTkLabel(footer, text="Grand Total: ₹0.00", font=("Arial", 20, "bold"), text_color="#2ecc71")
        self.total_lbl.pack(side="right", padx=20)
        
        ctk.CTkButton(footer, text="Complete Sale", fg_color="#27ae60", command=self.checkout).pack(side="left", padx=20)

        self.handle_search()

    def get_cart_qty(self, product_name):
        """Calculates how many units of a product are already in the cart."""
        return sum(item[4] for item in self.cart if item[1] == product_name)

    def handle_search(self):
        """Fetches products and adjusts stock display based on what's in the cart."""
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
        
        formatted_results = []
        for name, db_stock in db_results:
            # Subtract what is already in the cart from the database stock
            effective_stock = db_stock - self.get_cart_qty(name)
            formatted_results.append(f"{name} (Avail: {effective_stock})")
        
        self.res_dropdown.configure(values=formatted_results)
        if formatted_results:
            self.res_dropdown.set(formatted_results[0])
        else:
            self.res_dropdown.set("No results found")

    def add_to_cart(self):
        selected_raw = self.res_dropdown.get()
        if "No results found" in selected_raw: return

        # Parse the name out of "Name (Avail: X)"
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
            
            # Final Validation: DB Stock vs (In Cart + New Qty)
            if (current_in_cart + qty_to_add) > p_db_stock:
                messagebox.showerror("Stock Error", f"Insufficient Stock!\nIn Cart: {current_in_cart}\nMax Possible: {p_db_stock - current_in_cart}")
                return

            # Check if item exists in cart to merge rows
            found = False
            for item in self.cart:
                if item[0] == p_code:
                    item[4] += qty_to_add # Update Qty
                    item[5] = item[3] * item[4] # Update Total
                    found = True
                    break
            
            if not found:
                item_total = p_price * qty_to_add
                self.cart.append([p_code, p_name, p_cat, p_price, qty_to_add, item_total])

            # Refresh table and dropdown stock display
            self.refresh_table()
            self.update_total()
            self.handle_search() 
        
    def refresh_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for item in self.cart:
            self.tree.insert("", "end", values=item)

    def update_total(self):
        total = sum(i[5] for i in self.cart)
        self.total_lbl.configure(text=f"Grand Total: ₹{total:.2f}")

    def checkout(self):
        if not self.cart: return
        bill_id = f"BILL-{int(time.time())}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            for item in self.cart:
                p_code, p_name, p_cat, p_price, p_qty, p_total = item
                self.db.cursor.execute("UPDATE inventory SET stock=stock-?, sold_qty=sold_qty+? WHERE product_code=?", (p_qty, p_qty, p_code))
                self.db.cursor.execute("INSERT INTO sales (bill_id, item_name, category, quantity, total, date) VALUES (?,?,?,?,?,?)", (bill_id, p_name, p_cat, p_qty, p_total, now))
                logging.info(f"SOLD: {p_name} | Qty: {p_qty} | Total: {p_total}")

            self.db.conn.commit()
            messagebox.showinfo("Success", f"Bill {bill_id} Saved!")
            self.cart = []
            self.render()
        except Exception as e:
            logging.error(f"CHECKOUT ERROR: {str(e)}")
            messagebox.showerror("Error", "Checkout failed.")