import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import csv
import time
from datetime import datetime

class ReportsModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        """Method called by main.py to display the Reporting UI"""
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Advanced Sales Reports", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Search & Filter Section ---
        filter_frame = ctk.CTkFrame(self.main_view)
        filter_frame.pack(fill="x", padx=20, pady=10)

        # Bill ID Search
        ctk.CTkLabel(filter_frame, text="Bill ID:").grid(row=0, column=0, padx=5)
        self.search_bill = ctk.CTkEntry(filter_frame, placeholder_text="Search...", width=100)
        self.search_bill.grid(row=0, column=1, padx=5)
        self.search_bill.bind("<KeyRelease>", lambda e: self.refresh_data())

        # Date Filter Labels & Entries
        ctk.CTkLabel(filter_frame, text="From:").grid(row=0, column=2, padx=5)
        self.date_from = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD", width=110)
        self.date_from.grid(row=0, column=3, padx=5)

        ctk.CTkLabel(filter_frame, text="To:").grid(row=0, column=4, padx=5)
        self.date_to = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD", width=110)
        self.date_to.grid(row=0, column=5, padx=5)

        # Action Buttons
        ctk.CTkButton(filter_frame, text="Apply Filter", width=100, fg_color="#1f538d", 
                      command=self.refresh_data).grid(row=0, column=6, padx=5)
        
        ctk.CTkButton(filter_frame, text="Reset", width=80, fg_color="#7f8c8d", 
                      command=self.reset_filters).grid(row=0, column=7, padx=5)

        # --- Data Table ---
        columns = ("Bill ID", "Item Name", "Qty", "Total", "Date")
        self.tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Footer Summary & Export ---
        footer_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        footer_frame.pack(fill="x", padx=20, pady=10)

        self.revenue_lbl = ctk.CTkLabel(footer_frame, text="Revenue: ₹0.00", font=("Arial", 18, "bold"), text_color="#2ecc71")
        self.revenue_lbl.pack(side="left")

        ctk.CTkButton(footer_frame, text="📊 Export Full Order CSV", fg_color="#27ae60", 
                      command=self.export_csv).pack(side="right", padx=10)

        self.refresh_data() 

    def reset_filters(self):
        """Clears all input fields and reloads the full dataset"""
        self.search_bill.delete(0, 'end')
        self.date_from.delete(0, 'end')
        self.date_to.delete(0, 'end')
        self.refresh_data()

    def refresh_data(self):
        """Dynamic Search and Date Filtering"""
        bill_val = self.search_bill.get()
        d_from = self.date_from.get()
        d_to = self.date_to.get()

        query = "SELECT bill_id, item_name, quantity, total, date FROM sales WHERE 1=1"
        params = []

        if bill_val:
            query += " AND bill_id LIKE ?"
            params.append(f"%{bill_val}%")
        
        if d_from and d_to:
            query += " AND date BETWEEN ? AND ?"
            params.extend([d_from, d_to])

        query += " ORDER BY id DESC"
        
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        self.db.cursor.execute(query, params)
        rows = self.db.cursor.fetchall()
        
        total_revenue = 0
        for row in rows:
            self.tree.insert("", "end", values=row)
            total_revenue += row[3]
        
        self.revenue_lbl.configure(text=f"Total Revenue: ₹{total_revenue:.2f}")

    def export_csv(self):
        """Logic to export ALL rows matching the selected Bill ID"""
        selected_item = self.tree.selection()
        
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please click a row from the order you want to export.")
            return

        # Get Bill ID from the selected row
        bill_id = self.tree.item(selected_item)['values'][0]

        # Fetch every item sold under this specific bill
        self.db.cursor.execute(
            "SELECT bill_id, item_name, quantity, total, date FROM sales WHERE bill_id = ?", 
            (bill_id,)
        )
        data = self.db.cursor.fetchall()

        if not os.path.exists("exports"):
            os.makedirs("exports")
        
        path = f"exports/Full_Order_{bill_id}.csv"

        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Bill ID", "Item Name", "Qty", "Total Price", "Date"])
                writer.writerows(data)
            
            messagebox.showinfo("Export Success", f"Exported {len(data)} items for Order {bill_id}")
            os.startfile("exports")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save. Close the file if it is open.\n{e}")