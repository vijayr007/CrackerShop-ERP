import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import time
import os
from fpdf import FPDF

class BillingModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db
        self.cart = []

    def render(self):
        # Clear frame for a fresh load
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Point of Sale", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Search & Input Area ---
        search_frame = ctk.CTkFrame(self.main_view)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        self.search_in = ctk.CTkEntry(search_frame, placeholder_text="Start typing Name or Code...", width=300)
        self.search_in.grid(row=0, column=0, padx=10)
        # BIND DYNAMIC SEARCH
        self.search_in.bind("<KeyRelease>", self.dynamic_search)

        self.qty_in = ctk.CTkEntry(search_frame, placeholder_text="Qty", width=70)
        self.qty_in.grid(row=0, column=1, padx=10)
        self.qty_in.insert(0, "1")
        
        ctk.CTkButton(search_frame, text="Add to Cart", command=self.add_to_cart, fg_color="#2ecc71").grid(row=0, column=2, padx=10)

        # Dynamic Status Label
        self.status_lbl = ctk.CTkLabel(self.main_view, text="Suggestions: None", font=("Arial", 12, "italic"), text_color="gray")
        self.status_lbl.pack(anchor="w", padx=30)

        # --- Cart Table ---
        self.tree = ttk.Treeview(self.main_view, columns=("Code", "Name", "Price", "Qty", "Total"), show='headings')
        for col in ("Code", "Name", "Price", "Qty", "Total"): 
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.total_lbl = ctk.CTkLabel(self.main_view, text="Total: ₹0.00", font=("Arial", 22, "bold"))
        self.total_lbl.pack(pady=10)
        
        # --- Action Buttons ---
        action_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        action_frame.pack(pady=10)

        ctk.CTkButton(action_frame, text="Save Bill", command=self.submit_only, 
                      fg_color="#34495e", width=180, height=40).grid(row=0, column=0, padx=10)

        ctk.CTkButton(action_frame, text="Save & Print PDF", command=self.submit_and_print, 
                      fg_color="#1f538d", width=180, height=40).grid(row=0, column=1, padx=10)

    def dynamic_search(self, event):
        """Queries database as the user types."""
        val = self.search_in.get()
        if len(val) < 2:
            self.status_lbl.configure(text="Suggestions: None", text_color="gray")
            return

        # Look for partial matches
        self.db.cursor.execute("SELECT name, stock FROM inventory WHERE name LIKE ? OR product_code LIKE ? LIMIT 1", 
                              (f'%{val}%', f'%{val}%'))
        match = self.db.cursor.fetchone()
        
        if match:
            self.status_lbl.configure(text=f"Found: {match[0]} | Stock: {match[1]}", text_color="#2ecc71")
        else:
            self.status_lbl.configure(text="Product not found", text_color="#e74c3c")

    def add_to_cart(self):
        val = self.search_in.get()
        qty = self.qty_in.get()
        
        if not qty.isdigit() or not val: return
        
        self.db.cursor.execute("SELECT product_code, name, price, stock FROM inventory WHERE product_code=? OR name=?", (val, val))
        item = self.db.cursor.fetchone()
        
        if item:
            if item[3] >= int(qty):
                sub = item[2] * int(qty)
                self.cart.append((item[0], item[1], item[2], int(qty), sub))
                self.update_ui()
                # Reset for next item
                self.search_in.delete(0, 'end')
                self.search_in.focus()
            else:
                messagebox.showerror("Stock Error", f"Insufficient Stock! Only {item[3]} left.")
        else:
            messagebox.showerror("Error", "Product not found. Ensure the code/name is correct.")

    def update_ui(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        total = sum(item[4] for item in self.cart)
        for item in self.cart: self.tree.insert("", "end", values=item)
        self.total_lbl.configure(text=f"Total: ₹{total:.2f}")

    def _save_to_db(self):
        """Unified method to handle stock and sales records."""
        if not self.cart: return None
        bill_id = f"INV-{int(time.time())}"
        try:
            for item in self.cart:
                # Update inventory and sold tracking
                self.db.cursor.execute(
                    "UPDATE inventory SET stock = stock - ?, sold_qty = sold_qty + ? WHERE product_code = ?", 
                    (item[3], item[3], item[0])
                )
                # Record Sale with Bill ID
                self.db.cursor.execute(
                    "INSERT INTO sales (bill_id, item_name, quantity, total, date) VALUES (?,?,?,?,?)",
                    (bill_id, item[1], item[3], item[4], datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
            self.db.conn.commit()
            return bill_id
        except Exception as e:
            messagebox.showerror("DB Error", str(e))
            return None

    def submit_only(self):
        bill_id = self._save_to_db()
        if bill_id:
            messagebox.showinfo("Success", f"Bill {bill_id} saved.")
            self.cart = []; self.update_ui()

    def submit_and_print(self):
        total = sum(item[4] for item in self.cart)
        items_copy = list(self.cart)
        bill_id = self._save_to_db()
        if bill_id:
            path = self.generate_pdf(bill_id, total, items_copy)
            os.startfile(path) # Triggers system print/view
            self.cart = []; self.update_ui()

    def generate_pdf(self, bill_id, total, items):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "CRACKER SHOP BILL", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(190, 5, f"Bill ID: {bill_id} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
        pdf.ln(10)

        # Table Header
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(80, 10, "Item Name", 1); pdf.cell(30, 10, "Price", 1)
        pdf.cell(30, 10, "Qty", 1); pdf.cell(50, 10, "Total", 1); pdf.ln()

        # Items
        pdf.set_font("Arial", '', 10)
        for itm in items:
            pdf.cell(80, 10, str(itm[1]), 1)
            pdf.cell(30, 10, str(itm[2]), 1)
            pdf.cell(30, 10, str(itm[3]), 1)
            pdf.cell(50, 10, f"{itm[4]:.2f}", 1); pdf.ln()

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(140, 10, "Grand Total:", 1); pdf.cell(50, 10, f"Rs. {total:.2f}", 1)
        
        if not os.path.exists("receipts"): os.makedirs("receipts")
        path = f"receipts/{bill_id}.pdf"
        pdf.output(path)
        return path