import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import csv
import logging

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
        
        # Code is primary key (disabled during edit to prevent accidents)
        self.inv_code = ctk.CTkEntry(f, placeholder_text="Code", width=100)
        self.inv_code.grid(row=0, column=0, padx=5, pady=10)
        
        self.inv_name = ctk.CTkEntry(f, placeholder_text="Product Name", width=150)
        self.inv_name.grid(row=0, column=1, padx=5)

        # Dynamic Category Dropdown
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
        
        # Action Buttons
        ctk.CTkButton(f, text="Save/Update", width=100, command=self.save_item).grid(row=0, column=5, padx=5)
        ctk.CTkButton(f, text="Clear", width=80, fg_color="grey", command=self.clear_entries).grid(row=0, column=6, padx=5)
        # Inside render() method, likely in the button frame
        ctk.CTkButton(
            f, 
            text="📥 Import CSV", 
            fg_color="#3498db", 
            command=self.import_csv
        ).grid(row=0, column=7, padx=5)
        ctk.CTkButton(
            f, 
            text="📤 Export CSV", 
            fg_color="#27ae60", 
            hover_color="#1e8449", 
            command=self.export_csv
        ).grid(row=0, column=8, padx=5)
        
        # --- Table ---
        cols = ("Code", "Name", "Category", "Price", "Stock", "Sold Qty")
        self.tree = ttk.Treeview(self.main_view, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        
        # Bind Click Event to Table
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_list()

    def on_row_select(self, event):
        """Fills entry boxes with data from the selected row"""
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        row_values = self.tree.item(selected_item)['values']
        
        # Clear and Fill entries
        self.clear_entries()
        self.inv_code.insert(0, row_values[0])
        # Optional: Disable code editing during update to maintain DB integrity
        # self.inv_code.configure(state="disabled") 
        
        self.inv_name.insert(0, row_values[1])
        self.inv_cat.set(row_values[2])
        self.inv_price.insert(0, row_values[3])
        self.inv_stock.insert(0, row_values[4])

    def save_item(self):
        """Updates all fields based on the Product Code"""
        try:
            code = self.inv_code.get().upper()
            name = self.inv_name.get()
            cat = self.inv_cat.get()
            price = float(self.inv_price.get())
            stock = int(self.inv_stock.get())

            if not code or cat == "Select Category":
                messagebox.showwarning("Input Error", "Code and Category are required")
                return

            # SQL logic to update name, cat, price and stock if code exists
            # We use REPLACE or ON CONFLICT to ensure updates are complete
            self.db.cursor.execute("""
                INSERT INTO inventory (product_code, name, category, price, stock) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(product_code) 
                DO UPDATE SET 
                    name=excluded.name, 
                    category=excluded.category, 
                    price=excluded.price, 
                    stock=excluded.stock
            """, (code, name, cat, price, stock))
            
            self.db.conn.commit()
            logging.info(f"INVENTORY UPDATED: {code} | Name: {name}, Cat: {cat}, Price: {price}, Stock: {stock}")
            self.refresh_list()
            self.clear_entries()
            messagebox.showinfo("Success", f"Product {code} updated successfully.")
            
        except ValueError:
            messagebox.showerror("Error", "Check data types: Price (Decimal), Stock (Number)")

    def refresh_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute("SELECT product_code, name, category, price, stock, sold_qty FROM inventory")
        for row in self.db.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def clear_entries(self):
        self.inv_code.configure(state="normal")
        self.inv_code.delete(0, 'end')
        self.inv_name.delete(0, 'end')
        self.inv_price.delete(0, 'end')
        self.inv_stock.delete(0, 'end')
        self.inv_cat.set("Select Category")

    def import_csv(self):
        """
        Imports inventory from a CSV file.
        Required Headers: product_code, name, category, price, stock
        """
        path = filedialog.askopenfilename(
            title="Select Inventory CSV",
            filetypes=[("CSV Files", "*.csv")]
        )
        
        if not path:
            return

        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Validate headers before processing
                required_headers = {'product_code', 'name', 'category', 'price', 'stock'}
                if not required_headers.issubset(set(reader.fieldnames)):
                    messagebox.showerror("Header Error", f"CSV must contain: {', '.join(required_headers)}")
                    return

                count = 0
                for row in reader:
                    # SQL Upsert: Update if exists, Insert if new
                    self.db.cursor.execute("""
                        INSERT INTO inventory (product_code, name, category, price, stock) 
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(product_code) 
                        DO UPDATE SET 
                            name=excluded.name, 
                            category=excluded.category, 
                            price=excluded.price, 
                            stock=stock + excluded.stock
                    """, (
                        row['product_code'].upper(),
                        row['name'],
                        row['category'],
                        float(row['price']),
                        int(row['stock'])
                    ))
                    count += 1
                
                self.db.conn.commit()
                logging.info(f"CSV IMPORT SUCCESS: {count} items processed from {path}")
                messagebox.showinfo("Success", f"Successfully imported/updated {count} items.")
                self.refresh_list() # Refresh the UI table

        except Exception as e:
            logging.error(f"CSV IMPORT ERROR: {str(e)}")
            messagebox.showerror("Import Failed", f"An error occurred: {str(e)}")   

    def export_csv(self):
        """Exports all inventory data to a CSV file."""
        try:
            # Fetch current data from database
            self.db.cursor.execute("SELECT product_code, name, category, price, stock, sold_qty FROM inventory")
            rows = self.db.cursor.fetchall()
            
            if not rows:
                messagebox.showwarning("No Data", "There is no inventory data to export.")
                return

            # Open Save Dialog
            path = filedialog.asksaveasfilename(
                title="Save Inventory Export",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")],
                initialfile=f"Inventory_Report_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if not path:
                return

            # Write data to file
            with open(path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Standard Headers
                writer.writerow(["Product Code", "Name", "Category", "Price", "Stock", "Sold Qty"])
                writer.writerows(rows)
                
            logging.info(f"INVENTORY EXPORTED: {path}")
            messagebox.showinfo("Success", f"Data exported successfully to:\n{path}")
            
        except Exception as e:
            logging.error(f"EXPORT ERROR: {str(e)}")
            messagebox.showerror("Error", f"Failed to export CSV: {e}")            