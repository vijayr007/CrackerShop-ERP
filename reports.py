import customtkinter as ctk
from tkinter import ttk, messagebox
import os
import csv
import logging
from datetime import datetime
from fpdf import FPDF

class ReportsModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db
        # Fix: Ensure the export directory exists on startup
        if not os.path.exists("exports"):
            os.makedirs("exports")

    def render(self):
        """Standard method called by main.py to show the Reporting UI"""
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Sales Reports & Data Export", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Advanced Filter Section ---
        filter_frame = ctk.CTkFrame(self.main_view)
        filter_frame.pack(fill="x", padx=20, pady=10)

        # 1. Dynamic Bill ID Search
        ctk.CTkLabel(filter_frame, text="Bill ID:").grid(row=0, column=0, padx=5)
        self.search_bill = ctk.CTkEntry(filter_frame, placeholder_text="Search ID...", width=120)
        self.search_bill.grid(row=0, column=1, padx=5)
        self.search_bill.bind("<KeyRelease>", lambda e: self.refresh_data())

        # 2. Category Filter
        ctk.CTkLabel(filter_frame, text="Category:").grid(row=0, column=2, padx=5)
        self.db.cursor.execute("SELECT name FROM categories")
        categories = ["All"] + [r[0] for r in self.db.cursor.fetchall()]
        self.cat_filter = ctk.CTkComboBox(filter_frame, values=categories, width=130, command=lambda x: self.refresh_data())
        self.cat_filter.set("All")
        self.cat_filter.grid(row=0, column=3, padx=5)

        # 3. Date Based Search
        ctk.CTkLabel(filter_frame, text="From:").grid(row=1, column=0, padx=5, pady=10)
        available_dates = self.get_available_dates()
        self.date_from = ctk.CTkComboBox(filter_frame, values=available_dates, width=120)
        self.date_from.set("Select Date")
        self.date_from.grid(row=1, column=1, padx=5)

        ctk.CTkLabel(filter_frame, text="To:").grid(row=1, column=2, padx=5)
        self.date_to = ctk.CTkComboBox(filter_frame, values=available_dates, width=120)
        self.date_to.set("Select Date")
        self.date_to.grid(row=1, column=3, padx=5)

        # Buttons
        ctk.CTkButton(filter_frame, text="Apply Date Filter", width=120, command=self.refresh_data).grid(row=1, column=4, padx=10)
        ctk.CTkButton(filter_frame, text="Reset", fg_color="#7f8c8d", width=80, command=self.reset_filters).grid(row=1, column=5, padx=5)

        # --- Treeview Table ---
        columns = ("Bill ID", "Item Name", "Category", "Qty", "Total", "Date/Time")
        self.tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Action Footer ---
        action_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=10)

        self.revenue_lbl = ctk.CTkLabel(action_frame, text="Total Revenue: ₹0.00", font=("Arial", 18, "bold"), text_color="#2ecc71")
        self.revenue_lbl.pack(side="left")

        ctk.CTkButton(action_frame, text="📄 View PDF", fg_color="#34495e", command=self.export_pdf).pack(side="right", padx=5)
        ctk.CTkButton(action_frame, text="📊 Export CSV", fg_color="#27ae60", command=self.export_csv).pack(side="right", padx=5)

        self.refresh_data()

    def get_available_dates(self):
        self.db.cursor.execute("SELECT DISTINCT date(date) FROM sales ORDER BY date DESC")
        dates = [row[0] for row in self.db.cursor.fetchall()]
        return dates if dates else ["No Sales"]

    def reset_filters(self):
        self.search_bill.delete(0, 'end')
        self.cat_filter.set("All")
        self.date_from.set("Select Date")
        self.date_to.set("Select Date")
        self.refresh_data()

    def refresh_data(self):
        """Dynamic database query based on filters"""
        bill_val = self.search_bill.get().strip()
        cat_val = self.cat_filter.get()
        d_from = self.date_from.get()
        d_to = self.date_to.get()

        query = "SELECT bill_id, item_name, category, quantity, total, date FROM sales WHERE 1=1"
        params = []

        if bill_val:
            query += " AND bill_id LIKE ?"
            params.append(f"%{bill_val}%")
        if cat_val != "All":
            query += " AND category = ?"
            params.append(cat_val)
        if d_from != "Select Date" and d_to != "Select Date":
            query += " AND date(date) BETWEEN ? AND ?"
            params.extend([d_from, d_to])

        query += " ORDER BY date DESC"
        
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute(query, params)
        rows = self.db.cursor.fetchall()
        
        total_rev = 0
        for row in rows:
            self.tree.insert("", "end", values=row)
            total_rev += row[4]
        self.revenue_lbl.configure(text=f"Total Revenue: ₹{total_rev:.2f}")

    def generate_filename(self, ext):
        """Generates filename based on Bill ID or Date Range"""
        bill = self.search_bill.get().strip()
        dfrom = self.date_from.get()
        dto = self.date_to.get()

        if bill:
            name = f"Bill_{bill}"
        elif dfrom != "Select Date" and dto != "Select Date":
            name = f"Report_{dfrom}_to_{dto}"
        else:
            name = f"General_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return f"exports/{name}{ext}"

    def export_pdf(self):
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Empty", "No data to export.")
            return

        file_path = self.generate_filename(".pdf")
        
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "FIREWORKS SALES REPORT", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
            pdf.ln(10)

            # Table Header
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", 'B', 10)
            cols = ["Bill ID", "Item", "Cat", "Qty", "Total"]
            w = [40, 55, 35, 20, 40]
            for i in range(len(cols)):
                pdf.cell(w[i], 10, cols[i], 1, 0, 'C', True)
            pdf.ln()

            # Table Rows
            pdf.set_font("Arial", '', 9)
            grand_total = 0
            for item_id in items:
                v = self.tree.item(item_id)['values']
                pdf.cell(w[0], 8, str(v[0]), 1)
                pdf.cell(w[1], 8, str(v[1]), 1)
                pdf.cell(w[2], 8, str(v[2]), 1)
                pdf.cell(w[3], 8, str(v[3]), 1)
                pdf.cell(w[4], 8, f"Rs. {v[4]}", 1)
                pdf.ln()
                grand_total += float(v[4])

            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 10, f"Grand Total Revenue: Rs. {grand_total:.2f}", 0, 1, 'R')

            pdf.output(file_path)
            
            # Final check before opening
            if os.path.exists(file_path):
                os.startfile(os.path.abspath(file_path))
        except Exception as e:
            messagebox.showerror("Error", f"PDF Failed: {e}")

    def export_csv(self):
        items = self.tree.get_children()
        if not items: return
        
        file_path = self.generate_filename(".csv")
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Bill ID", "Item", "Category", "Qty", "Total", "Timestamp"])
                for item_id in items:
                    writer.writerow(self.tree.item(item_id)['values'])
            messagebox.showinfo("Success", f"Saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"CSV Failed: {e}")