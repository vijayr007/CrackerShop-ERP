import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import time, os
from fpdf import FPDF

class BillingModule:
    def __init__(self, main_view, db):
        self.main_view, self.db, self.cart = main_view, db, []

    def render(self):
        for w in self.main_view.winfo_children(): w.destroy()
        ctk.CTkLabel(self.main_view, text="Point of Sale", font=("Arial", 22, "bold")).pack(pady=10)
        
        sf = ctk.CTkFrame(self.main_view)
        sf.pack(fill="x", padx=20, pady=10)
        
        self.search_in = ctk.CTkEntry(sf, placeholder_text="Search Name/Code...", width=250)
        self.search_in.grid(row=0, column=0, padx=10)
        self.search_in.bind("<KeyRelease>", self.dynamic_search)
        
        self.qty_in = ctk.CTkEntry(sf, placeholder_text="Qty", width=70)
        self.qty_in.grid(row=0, column=1, padx=10); self.qty_in.insert(0, "1")
        
        ctk.CTkButton(sf, text="Add", command=self.add_to_cart).grid(row=0, column=2, padx=10)
        self.status = ctk.CTkLabel(self.main_view, text="Suggestion: None", font=("Arial", 12, "italic"))
        self.status.pack(anchor="w", padx=30)

        self.tree = ttk.Treeview(self.main_view, columns=("Code", "Name", "Price", "Qty", "Total"), show='headings')
        for col in ("Code", "Name", "Price", "Qty", "Total"): self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        self.total_lbl = ctk.CTkLabel(self.main_view, text="Total: ₹0.00", font=("Arial", 20, "bold"))
        self.total_lbl.pack(pady=10)
        
        btn_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        btn_f.pack(pady=10)
        ctk.CTkButton(btn_f, text="Save Only", fg_color="#34495e", command=self.save_only).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_f, text="Save & Print PDF", command=self.save_print).grid(row=0, column=1, padx=10)

    def dynamic_search(self, e):
        v = self.search_in.get()
        if len(v) < 2: return
        self.db.cursor.execute("SELECT name, stock FROM inventory WHERE name LIKE ? OR product_code LIKE ? LIMIT 1", (f'%{v}%', f'%{v}%'))
        res = self.db.cursor.fetchone()
        self.status.configure(text=f"Found: {res[0]} (Stock: {res[1]})" if res else "Not Found")

    def add_to_cart(self):
        v, q = self.search_in.get(), self.qty_in.get()
        self.db.cursor.execute("SELECT product_code, name, price, stock FROM inventory WHERE product_code=? OR name=?", (v, v))
        it = self.db.cursor.fetchone()
        if it and it[3] >= int(q):
            self.cart.append((it[0], it[1], it[2], int(q), it[2]*int(q)))
            self.update_ui(); self.search_in.delete(0, 'end')
        else: messagebox.showerror("Error", "Check Stock/Code")

    def update_ui(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        total = sum(i[4] for i in self.cart)
        for i in self.cart: self.tree.insert("", "end", values=i)
        self.total_lbl.configure(text=f"Total: ₹{total:.2f}")

    def _finalize_db(self):
        if not self.cart: return None
        bid = f"INV-{int(time.time())}"
        for i in self.cart:
            self.db.cursor.execute("UPDATE inventory SET stock=stock-?, sold_qty=sold_qty+? WHERE product_code=?", (i[3], i[3], i[0]))
            self.db.cursor.execute("INSERT INTO sales VALUES (NULL,?,?,?,?,?)", (bid, i[1], i[3], i[4], datetime.now().strftime("%Y-%m-%d")))
        self.db.conn.commit()
        return bid

    def save_only(self):
        if self._finalize_db():
            messagebox.showinfo("Success", "Saved"); self.cart = []; self.update_ui()

    def save_print(self):
        total = sum(i[4] for i in self.cart); items = list(self.cart)
        bid = self._finalize_db()
        if bid:
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "INVOICE", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            for i in items: pdf.cell(190, 8, f"{i[1]} x {i[3]} = {i[4]}", ln=True)
            pdf.cell(190, 10, f"Total: Rs.{total}", ln=True)
            if not os.path.exists("receipts"): os.makedirs("receipts")
            path = f"receipts/{bid}.pdf"; pdf.output(path); os.startfile(path)
            self.cart = []; self.update_ui()