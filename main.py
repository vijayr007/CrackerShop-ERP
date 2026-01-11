import customtkinter as ctk
from database import db
from inventory import InventoryModule
from billing import BillingModule
from reports import ReportsModule
from users import UserManagementModule
from categories import CategoryModule
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
        
        self.title(f"CrackerShop - {self.username}")
        self.geometry("1200x750")

        # Layout
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.main_view = ctk.CTkFrame(self, corner_radius=15)
        self.main_view.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Menu Buttons
        ctk.CTkLabel(self.sidebar, text="MAIN MENU", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Public Buttons
        ctk.CTkButton(self.sidebar, text="💳 Billing", command=lambda: self.load_module("bill")).pack(fill="x", padx=10, pady=5)
        
        # Admin Only Buttons
        if self.user_role == "Admin":
            ctk.CTkButton(self.sidebar, text="📦 Inventory", command=lambda: self.load_module("inv")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="📁 Categories", command=lambda: self.load_module("cat")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="📊 Reports", command=lambda: self.load_module("rep")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="👥 Users", command=lambda: self.load_module("usr")).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#c0392b", command=self.logout).pack(side="bottom", pady=20)
        
        # Initial View
        self.load_module("bill")

    def load_module(self, mod):
        # Clear existing widgets
        for widget in self.main_view.winfo_children():
            widget.destroy()
            
        # Router logic - Removed duplicated "cat" block
        if mod == "bill":
            BillingModule(self.main_view, db).render()
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
    app = LoginWindow(lambda u, r: CrackerApp(u, r).mainloop())
    app.mainloop()

if __name__ == "__main__":
    main()