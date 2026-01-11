import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import csv
import logging
from datetime import datetime

class InventoryModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Inventory Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Entry Form ---
        f = ctk.CTkFrame(self.main_view)
        f.pack(fill="x", padx=20, pady=10)
        
        # All inputs on one row for a streamlined look
        self.inv_code = ctk.CTkEntry(f, placeholder_text="Code", width=100)
        self.inv_code.grid(row=0, column=0, padx=5, pady=10)
        
        self.inv_name = ctk.CTkEntry(f, placeholder_text="Product Name", width=150)
        self.inv_name.grid(row=0, column=1, padx=5)

        self.db.cursor.execute("SELECT name FROM categories")
        cat_list = [r[0] for r in self.db.cursor.fetchall()]
        if not cat_list: cat_list = ["General"]

        self.inv_cat = ctk.CTkComboBox(f, values=cat_list, width=130)
        self.inv_cat.grid(row=0, column=2, padx=5)
        self.inv_cat.set("Select Category")
        
        self.inv_price = ctk.CTkEntry(f, placeholder_text="Price", width=80)
        self.inv_price.grid(row=0, column=3, padx=5)
        
        self.inv_stock = ctk.CTkEntry(f, placeholder_text="Stock", width=80)
        self.inv_stock.grid(row=0, column=4, padx=5)

        self.inv_disc = ctk.CTkEntry(f, placeholder_text="Disc %", width=60)
        self.inv_disc.grid(row=0, column=5, padx=5)
        self.inv_disc.insert(0, "0")
        
        # Action Buttons
        ctk.CTkButton(f, text="Save/Update", width=100, command=self.save_item).grid(row=0, column=6, padx=5)
        ctk.CTkButton(f, text="Clear", width=60, fg_color="grey", command=self.clear_entries).grid(row=0, column=7, padx=5)

        # --- Utility Bar (Search & CSV) ---
        util_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        util_f.pack(fill="x", padx=20, pady=5)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_list())
        ctk.CTkEntry(util_f, placeholder_text="🔍 Filter items...", textvariable=self.search_var, width=250).pack(side="left")

        ctk.CTkButton(util_f, text="📤 Export CSV", fg_color="#27ae60", width=100, command=self.export_csv).pack(side="right", padx=5)
        ctk.CTkButton(util_f, text="📥 Import CSV", fg_color="#3498db", width=100, command=self.import_csv).pack(side="right", padx=5)

        # --- Table ---
        cols = ("Code", "Name", "Category", "Price", "Stock", "Disc %", "Sold Qty")
        self.tree = ttk.Treeview(self.main_view, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_list()

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        v = self.tree.item(selected[0])['values']
        self.clear_entries()
        self.inv_code.insert(0, v[0])
        self.inv_name.insert(0, v[1])
        self.inv_cat.set(v[2])
        self.inv_price.insert(0, v[3])
        self.inv_stock.insert(0, v[4])
        self.inv_disc.delete(0, 'end')
        self.inv_disc.insert(0, v[5])

    def save_item(self):
        try:
            code = self.inv_code.get().upper()
            name, cat = self.inv_name.get(), self.inv_cat.get()
            price, stock = float(self.inv_price.get()), int(self.inv_stock.get())
            disc = float(self.inv_disc.get())

            if not code or cat == "Select Category":
                messagebox.showwarning("Error", "Missing required fields")
                return

            self.db.cursor.execute("""
                INSERT INTO inventory (product_code, name, category, price, stock, discount_percent) 
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_code) 
                DO UPDATE SET name=excluded.name, category=excluded.category, 
                              price=excluded.price, stock=excluded.stock, 
                              discount_percent=excluded.discount_percent
            """, (code, name, cat, price, stock, disc))
            
            self.db.conn.commit()
            self.refresh_list()
            self.clear_entries()
            messagebox.showinfo("Success", f"Product {code} updated.")
        except ValueError:
            messagebox.showerror("Error", "Check numeric fields: Price, Stock, and Disc %")

    def refresh_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        search = f"%{self.search_var.get()}%"
        self.db.cursor.execute("""
            SELECT product_code, name, category, price, stock, discount_percent, sold_qty 
            FROM inventory 
            WHERE name LIKE ? OR product_code LIKE ?
        """, (search, search))
        for row in self.db.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def clear_entries(self):
        for entry in [self.inv_code, self.inv_name, self.inv_price, self.inv_stock]:
            entry.delete(0, 'end')
        self.inv_disc.delete(0, 'end')
        self.inv_disc.insert(0, "0")
        self.inv_cat.set("Select Category")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not path: return
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    disc = row.get('discount_percent', 0)
                    self.db.cursor.execute("""
                        INSERT INTO inventory (product_code, name, category, price, stock, discount_percent) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(product_code) DO UPDATE SET 
                        name=excluded.name, price=excluded.price, 
                        stock=stock + excluded.stock, discount_percent=excluded.discount_percent
                    """, (row['product_code'].upper(), row['name'], row['category'], 
                          float(row['price']), int(row['stock']), float(disc)))
            self.db.conn.commit()
            self.refresh_list()
            messagebox.showinfo("Success", "Import Complete.")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def export_csv(self):
        self.db.cursor.execute("SELECT product_code, name, category, price, stock, discount_percent, sold_qty FROM inventory")
        rows = self.db.cursor.fetchall()
        if not rows: return
        path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                            initialfile=f"Inventory_{datetime.now().strftime('%d%m%Y')}.csv")
        if not path: return
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["product_code", "name", "category", "price", "stock", "discount_percent", "sold_qty"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Saved to {path}")