import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import os
from fpdf import FPDF

class ReportsModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        # Clear existing widgets to refresh the view
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Detailed Sales Report", font=("Arial", 22, "bold")).pack(pady=10)
        
        # Summary Header (Optional but useful)
        self.db.cursor.execute("SELECT SUM(total) FROM sales")
        total_revenue = self.db.cursor.fetchone()[0] or 0
        ctk.CTkLabel(self.main_view, text=f"Total Revenue: ₹{total_revenue:.2f}", 
                     font=("Arial", 16), text_color="#2ecc71").pack(pady=5)

        # Treeview setup for UI data display
        columns = ("Bill ID", "Item", "Qty", "Total", "Date")
        tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns: 
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        
        # Querying data from database
        self.db.cursor.execute("SELECT bill_id, item_name, quantity, total, date FROM sales ORDER BY id DESC")
        for row in self.db.cursor.fetchall(): 
            tree.insert("", "end", values=row)
            
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Action Buttons for PDF Export
        btn_frame = ctk.CTkFrame(self.main_view)
        btn_frame.pack(pady=10, fill="x", padx=20)
        
        ctk.CTkButton(btn_frame, text="Export Today's PDF", 
                      command=lambda: self.export_report_pdf("Day")).grid(row=0, column=0, padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Export Monthly PDF", 
                      command=lambda: self.export_report_pdf("Month")).grid(row=0, column=1, padx=20, pady=10)

    def export_report_pdf(self, period="Day"):
        try:
            # Determine date filter
            if period == "Day":
                date_filter = datetime.now().strftime("%Y-%m-%d")
            else:
                date_filter = datetime.now().strftime("%Y-%m") # Matches any day in the current month

            # Fetch filtered data
            self.db.cursor.execute("SELECT bill_id, item_name, quantity, total, date FROM sales WHERE date LIKE ?", (f"{date_filter}%",))
            rows = self.db.cursor.fetchall()

            if not rows:
                messagebox.showwarning("No Data", f"No sales found for this {period.lower()}.")
                return

            # Initialize PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"Cracker Shop Sales Report ({period} View)", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
            pdf.ln(5)

            # PDF Table Header
            pdf.set_fill_color(200, 200, 200)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(40, 10, "Bill ID", 1, 0, 'C', True)
            pdf.cell(60, 10, "Item Name", 1, 0, 'C', True)
            pdf.cell(20, 10, "Qty", 1, 0, 'C', True)
            pdf.cell(30, 10, "Total", 1, 0, 'C', True)
            pdf.cell(40, 10, "Date", 1, 1, 'C', True)

            # Table Rows
            pdf.set_font("Arial", '', 10)
            grand_total = 0
            for row in rows:
                pdf.cell(40, 8, str(row[0]), 1)
                pdf.cell(60, 8, str(row[1]), 1)
                pdf.cell(20, 8, str(row[2]), 1, 0, 'C')
                pdf.cell(30, 8, f"{row[3]:.2f}", 1, 0, 'R')
                pdf.cell(40, 8, str(row[4]), 1, 1, 'C')
                grand_total += row[3]

            pdf.set_font("Arial", 'B', 11)
            pdf.cell(120, 10, "Total Revenue:", 1, 0, 'R')
            pdf.cell(70, 10, f"Rs. {grand_total:.2f}", 1, 1, 'C')

            # Ensure directory exists and save
            if not os.path.exists('reports'):
                os.makedirs('reports')
            
            filename = f"reports/Sales_Report_{period}_{date_filter}.pdf"
            pdf.output(filename)
            
            # Open PDF automatically
            os.startfile(filename)
            messagebox.showinfo("Success", f"Report saved: {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred: {str(e)}")