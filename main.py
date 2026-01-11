import customtkinter as ctk
from database import db
from inventory import InventoryModule
from billing import BillingModule
from reports import ReportsModule
from users import UserManagementModule
from categories import CategoryModule
from customers import CustomerModule
from dashboard import DashboardModule  # New Dashboard Import
from tkinter import messagebox
import logging

class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.title("CrackerShop Login")
        self.geometry("400x350")
        self.on_success = on_success

        ctk.CTkLabel(self, text="FIREWORKS ERP", font=("Arial", 24, "bold")).pack(pady=20)
        self.u_in = ctk.CTkEntry(self, placeholder_text="Username", width=200)
        self.u_in.pack(pady=10)
        self.p_in = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=200)
        self.p_in.pack(pady=10)
        ctk.CTkButton(self, text="Login", command=self.login).pack(pady=20)

    def login(self):
        u, p = self.u_in.get(), self.p_in.get()
        db.cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
        res = db.cursor.fetchone()
        if res:
            role = res[0]
            logging.info(f"User {u} logged in successfully with role {role}")
            self.destroy() 
            self.on_success(u, role)
        else:
            logging.warning(f"Failed login attempt for username: {u}")
            messagebox.showerror("Error", "Invalid Credentials")

class CrackerApp(ctk.CTk):
    def __init__(self, username, user_role):
        super().__init__()
        self.username = username
        self.user_role = user_role
        
        self.title(f"CrackerShop - {self.username} ({self.user_role})")
        self.geometry("1200x750")

        # Sidebar setup
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        # Main content area setup
        self.main_view = ctk.CTkFrame(self, corner_radius=15)
        self.main_view.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Sidebar Menu
        ctk.CTkLabel(self.sidebar, text="MAIN MENU", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Dashboard (Public)
        ctk.CTkButton(self.sidebar, text="📊 Dashboard", command=lambda: self.load_module("dash")).pack(fill="x", padx=10, pady=5)
        
        # Billing & Customers (Public)
        ctk.CTkButton(self.sidebar, text="💳 Billing", command=lambda: self.load_module("bill")).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.sidebar, text="👥 Customers", command=lambda: self.load_module("cust")).pack(fill="x", padx=10, pady=5)
        
        # Admin Only Section
        if self.user_role == "Admin":
            ctk.CTkLabel(self.sidebar, text="ADMIN TOOLS", font=("Arial", 12, "italic"), text_color="gray").pack(pady=(15, 5))
            ctk.CTkButton(self.sidebar, text="📦 Inventory", command=lambda: self.load_module("inv")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="📁 Categories", command=lambda: self.load_module("cat")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="📊 Reports", command=lambda: self.load_module("rep")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="⚙️ Users", command=lambda: self.load_module("usr")).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#c0392b", hover_color="#962d22", command=self.logout).pack(side="bottom", pady=20)
        
        # Load Dashboard by default on startup
        self.load_module("dash")

    def load_module(self, mod):
        # Clean current screen
        for widget in self.main_view.winfo_children():
            widget.destroy()
            
        # Module Routing
        if mod == "dash":
            DashboardModule(self.main_view, db).render()
        elif mod == "bill":
            BillingModule(self.main_view, db, self.username).render()
        elif mod == "cust":
            CustomerModule(self.main_view, db).render()
        elif mod == "inv":
            InventoryModule(self.main_view, db).render()
        elif mod == "cat":
            CategoryModule(self.main_view, db).render()
        elif mod == "rep":
            ReportsModule(self.main_view, db).render()
        elif mod == "usr":
            UserManagementModule(self.main_view, db).render()

    def logout(self):
        logging.info(f"User {self.username} logged out.")
        self.destroy()
        main()

def main():
    # Setup log formatting
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    app = LoginWindow(lambda u, r: CrackerApp(u, r).mainloop())
    app.mainloop()

if __name__ == "__main__":
    main()