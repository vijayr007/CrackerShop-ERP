import customtkinter as ctk
from tkinter import messagebox, ttk

class InventoryModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        # Clear frame
        for widget in self.main_view.winfo_children(): widget.destroy()

        ctk.CTkLabel(self.main_view, text="Inventory & Stock Tracking", font=("Arial", 22, "bold")).pack(pady=10)
        
        # Entry Section
        entry_frame = ctk.CTkFrame(self.main_view)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        self.inv_code = ctk.CTkEntry(entry_frame, placeholder_text="SKU/Code", width=100)
        self.inv_code.grid(row=0, column=0, padx=5, pady=10)
        
        self.inv_name = ctk.CTkEntry(entry_frame, placeholder_text="Item Name", width=150)
        self.inv_name.grid(row=0, column=1, padx=5)
        
        self.inv_price = ctk.CTkEntry(entry_frame, placeholder_text="Price", width=70)
        self.inv_price.grid(row=0, column=2, padx=5)
        
        self.inv_stock = ctk.CTkEntry(entry_frame, placeholder_text="Add Stock", width=70)
        self.inv_stock.grid(row=0, column=3, padx=5)
        
        # Buttons
        ctk.CTkButton(entry_frame, text="Add/Update Item", fg_color="#2ecc71", 
                      command=self.save_item).grid(row=0, column=4, padx=5)
        
        # Treeview with "Sold" column
        columns = ("Code", "Name", "Price", "Available Stock", "Total Sold")
        self.tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns: 
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_data()

    def save_item(self):
        """Logic to either Insert new or Update existing stock."""
        code = self.inv_code.get()
        name = self.inv_name.get()
        price = self.inv_price.get()
        added_stock = self.inv_stock.get()

        if not (code and added_stock):
            messagebox.showwarning("Input Error", "Code and Stock are required.")
            return

        try:
            # Check if product exists
            self.db.cursor.execute("SELECT stock FROM inventory WHERE product_code=?", (code,))
            result = self.db.cursor.fetchone()

            if result:
                # UPDATE: Add new stock to existing stock
                new_total = result[0] + int(added_stock)
                self.db.cursor.execute(
                    "UPDATE inventory SET price=?, stock=? WHERE product_code=?",
                    (float(price), new_total, code)
                )
                messagebox.showinfo("Success", f"Stock updated for {code}")
            else:
                # INSERT: Create new record
                self.db.cursor.execute(
                    "INSERT INTO inventory (product_code, name, price, stock, sold_qty) VALUES (?,?,?,?,0)",
                    (code, name, float(price), int(added_stock))
                )
                messagebox.showinfo("Success", "New Product Added")

            self.db.conn.commit()
            self.refresh_data()
            self.clear_entries()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def refresh_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        # Fetch data including the sold_qty
        self.db.cursor.execute("SELECT product_code, name, price, stock, sold_qty FROM inventory")
        for row in self.db.cursor.fetchall(): 
            self.tree.insert("", "end", values=row)

    def clear_entries(self):
        self.inv_code.delete(0, 'end')
        self.inv_name.delete(0, 'end')
        self.inv_price.delete(0, 'end')
        self.inv_stock.delete(0, 'end')