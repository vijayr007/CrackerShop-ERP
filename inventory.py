import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import os
import csv

class InventoryModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        # Clear frame
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Inventory Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Top Entry & Action Frame ---
        action_frame = ctk.CTkFrame(self.main_view)
        action_frame.pack(fill="x", padx=20, pady=10)
        
        # Manual Entry Fields (Existing Logic)
        self.inv_code = ctk.CTkEntry(action_frame, placeholder_text="Code", width=100)
        self.inv_code.grid(row=0, column=0, padx=5, pady=10)
        
        self.inv_name = ctk.CTkEntry(action_frame, placeholder_text="Item Name", width=150)
        self.inv_name.grid(row=0, column=1, padx=5)
        
        self.inv_price = ctk.CTkEntry(action_frame, placeholder_text="Price", width=70)
        self.inv_price.grid(row=0, column=2, padx=5)
        
        self.inv_stock = ctk.CTkEntry(action_frame, placeholder_text="Add Stock", width=70)
        self.inv_stock.grid(row=0, column=3, padx=5)
        
        ctk.CTkButton(action_frame, text="Update/Add", width=100, command=self.save_item).grid(row=0, column=4, padx=5)

        # --- NEW: Bulk Import Button ---
        ctk.CTkButton(action_frame, text="📥 Import CSV", fg_color="#3498db", width=100, 
                      command=self.import_csv).grid(row=0, column=5, padx=20)

        # --- Treeview ---
        columns = ("Code", "Name", "Price", "Available Stock", "Total Sold")
        self.tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_data()

    def import_csv(self):
        """Allows user to select a CSV file and imports data into DB."""
        file_path = filedialog.askopenfilename(
            title="Select Inventory CSV",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if not file_path:
            return

        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                import_count = 0
                update_count = 0

                for row in reader:
                    code = row['product_code']
                    name = row['name']
                    price = float(row['price'])
                    stock = int(row['stock'])

                    # Check if exists
                    self.db.cursor.execute("SELECT stock FROM inventory WHERE product_code=?", (code,))
                    result = self.db.cursor.fetchone()

                    if result:
                        # Update existing: Add to current stock
                        new_stock = result[0] + stock
                        self.db.cursor.execute(
                            "UPDATE inventory SET name=?, price=?, stock=? WHERE product_code=?",
                            (name, price, new_stock, code)
                        )
                        update_count += 1
                    else:
                        # Insert new
                        self.db.cursor.execute(
                            "INSERT INTO inventory (product_code, name, price, stock, sold_qty) VALUES (?,?,?,?,0)",
                            (code, name, price, stock)
                        )
                        import_count += 1
                
                self.db.conn.commit()
                self.refresh_data()
                messagebox.showinfo("Import Complete", f"Imported: {import_count}\nUpdated: {update_count}")

        except KeyError:
            messagebox.showerror("Format Error", "CSV must have headers: product_code, name, price, stock")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {e}")

    def save_item(self):
        """Manual save/update logic (as previously implemented)"""
        code = self.inv_code.get()
        name = self.inv_name.get()
        price = self.inv_price.get()
        stock = self.inv_stock.get()

        if not (code and stock):
            messagebox.showwarning("Error", "Code and Stock are required")
            return

        self.db.cursor.execute("SELECT stock FROM inventory WHERE product_code=?", (code,))
        res = self.db.cursor.fetchone()
        if res:
            new_total = res[0] + int(stock)
            self.db.cursor.execute("UPDATE inventory SET price=?, stock=? WHERE product_code=?", (float(price), new_total, code))
        else:
            self.db.cursor.execute("INSERT INTO inventory (product_code, name, price, stock, sold_qty) VALUES (?,?,?,?,0)", (code, name, float(price), int(stock)))
        
        self.db.conn.commit()
        self.refresh_data()

    def refresh_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute("SELECT product_code, name, price, stock, sold_qty FROM inventory")
        for row in self.db.cursor.fetchall():
            self.tree.insert("", "end", values=row)