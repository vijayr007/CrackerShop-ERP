import customtkinter as ctk
from tkinter import ttk

class DashboardModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Business Analytics Dashboard", font=("Arial", 24, "bold")).pack(pady=20)

        # --- Top Stats Row ---
        stats_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)

        total_value = self.get_total_inventory_value()
        low_stock_count = self.get_low_stock_count()
        total_sales = self.get_total_sales_count()

        self.create_stat_card(stats_frame, "Stock Value", f"₹{total_value:,.2f}", "#2ecc71").grid(row=0, column=0, padx=10)
        self.create_stat_card(stats_frame, "Low Stock Items", str(low_stock_count), "#e74c3c").grid(row=0, column=1, padx=10)
        self.create_stat_card(stats_frame, "Items Sold (Total)", str(total_sales), "#3498db").grid(row=0, column=2, padx=10)

        # --- Data Section ---
        data_frame = ctk.CTkFrame(self.main_view)
        data_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Column: Category Performance
        ctk.CTkLabel(data_frame, text="Category Performance (Units Sold)", font=("Arial", 16, "bold")).grid(row=0, column=0, padx=20, pady=10)
        
        self.cat_tree = ttk.Treeview(data_frame, columns=("Cat", "Qty"), show="headings", height=8)
        self.cat_tree.heading("Cat", text="Category")
        self.cat_tree.heading("Qty", text="Units Sold")
        self.cat_tree.grid(row=1, column=0, padx=20, pady=5)

        # Right Column: Top 5 Best Sellers
        ctk.CTkLabel(data_frame, text="Top 5 Best Selling Items", font=("Arial", 16, "bold")).grid(row=0, column=1, padx=20, pady=10)
        
        self.top_tree = ttk.Treeview(data_frame, columns=("Item", "Sold"), show="headings", height=8)
        self.top_tree.heading("Item", text="Product Name")
        self.top_tree.heading("Sold", text="Qty Sold")
        self.top_tree.grid(row=1, column=1, padx=20, pady=5)

        self.load_dashboard_data()

    def create_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent, width=200, height=100, border_width=2, border_color=color)
        ctk.CTkLabel(card, text=title, font=("Arial", 14)).pack(pady=5)
        ctk.CTkLabel(card, text=value, font=("Arial", 20, "bold"), text_color=color).pack(pady=5)
        return card

    def get_total_inventory_value(self):
        self.db.cursor.execute("SELECT SUM(price * stock) FROM inventory")
        res = self.db.cursor.fetchone()[0]
        return res if res else 0.0

    def get_low_stock_count(self):
        self.db.cursor.execute("SELECT COUNT(*) FROM inventory WHERE stock < 10")
        return self.db.cursor.fetchone()[0]

    def get_total_sales_count(self):
        self.db.cursor.execute("SELECT SUM(sold_qty) FROM inventory")
        res = self.db.cursor.fetchone()[0]
        return res if res else 0

    def load_dashboard_data(self):
        # Category Data
        self.db.cursor.execute("SELECT category, SUM(sold_qty) as total FROM inventory GROUP BY category ORDER BY total DESC")
        for row in self.db.cursor.fetchall():
            self.cat_tree.insert("", "end", values=row)

        # Top Sellers Data
        self.db.cursor.execute("SELECT name, sold_qty FROM inventory ORDER BY sold_qty DESC LIMIT 5")
        for row in self.db.cursor.fetchall():
            self.top_tree.insert("", "end", values=row)