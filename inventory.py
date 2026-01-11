import customtkinter as ctk
from tkinter import messagebox, ttk

class InventoryModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        ctk.CTkLabel(self.main_view, text="Inventory Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        entry_frame = ctk.CTkFrame(self.main_view)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        self.inv_code = ctk.CTkEntry(entry_frame, placeholder_text="SKU/Code", width=100)
        self.inv_code.grid(row=0, column=0, padx=5, pady=10)
        self.inv_name = ctk.CTkEntry(entry_frame, placeholder_text="Item Name", width=150)
        self.inv_name.grid(row=0, column=1, padx=5)
        self.inv_cat = ctk.CTkComboBox(entry_frame, values=["Sparklers", "Crackers", "Rockets"], width=120)
        self.inv_cat.grid(row=0, column=2, padx=5)
        self.inv_price = ctk.CTkEntry(entry_frame, placeholder_text="Price", width=70)
        self.inv_price.grid(row=0, column=3, padx=5)
        self.inv_stock = ctk.CTkEntry(entry_frame, placeholder_text="Qty", width=70)
        self.inv_stock.grid(row=0, column=4, padx=5)
        
        ctk.CTkButton(entry_frame, text="Add Item", fg_color="#2ecc71", command=self.add_item).grid(row=0, column=5, padx=5)

        self.tree = self.create_treeview()
        self.refresh_data()

    def add_item(self):
        try:
            self.db.cursor.execute(
                "INSERT INTO inventory (product_code, name, category, price, stock) VALUES (?,?,?,?,?)",
                (self.inv_code.get(), self.inv_name.get(), self.inv_cat.get(), 
                 float(self.inv_price.get()), int(self.inv_stock.get()))
            )
            self.db.conn.commit()
            self.refresh_data()
            messagebox.showinfo("Success", "Product Added")
        except:
            messagebox.showerror("Error", "Product Code must be unique or missing fields")

    def refresh_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute("SELECT product_code, name, category, price, stock FROM inventory")
        for row in self.db.cursor.fetchall(): self.tree.insert("", "end", values=row)

    def create_treeview(self):
        columns = ("Code", "Name", "Category", "Price", "Stock")
        tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns: tree.heading(col, text=col)
        tree.pack(fill="both", expand=True, padx=20, pady=10)
        return tree