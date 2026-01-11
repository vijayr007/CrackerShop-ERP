import customtkinter as ctk
from database import db
from inventory import InventoryModule
from billing import BillingModule
from reports import ReportsModule
from users import UserManagementModule
from tkinter import messagebox

class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.title("CrackerShop Login")
        self.geometry("400x350")
        self.on_success = on_success

        ctk.CTkLabel(self, text="CrackerShop ERP", font=("Arial", 24, "bold")).pack(pady=20)
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
            user_role = res[0]
            self.destroy() 
            self.on_success(u, user_role)
        else:
            messagebox.showerror("Error", "Invalid Credentials")

class CrackerApp(ctk.CTk):
    def __init__(self, username, user_role):
        super().__init__()
        # 1. Initialize custom variables FIRST
        self.user_role = user_role 
        self.username = username
        
        # 2. Setup Window
        self.title(f"CrackerShop ERP - {self.username}")
        self.geometry("1100x700")

        # 3. Setup UI
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.main_view = ctk.CTkFrame(self, corner_radius=15)
        self.main_view.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.sidebar, text="MENU", font=("Arial", 18, "bold")).pack(pady=20)
        
        # --- RBAC Logic ---
        ctk.CTkButton(self.sidebar, text="💳 Billing", command=lambda: self.load_module("bill")).pack(fill="x", padx=10, pady=5)
        
        if self.user_role == "Admin":
            ctk.CTkButton(self.sidebar, text="📦 Inventory", command=lambda: self.load_module("inv")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="📊 Reports", command=lambda: self.load_module("rep")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="👥 Users", command=lambda: self.load_module("usr")).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(self.sidebar, text="Logout", fg_color="red", command=self.logout).pack(side="bottom", pady=20)
        
        self.load_module("bill")

    def load_module(self, mod):
        for widget in self.main_view.winfo_children():
            widget.destroy()
            
        if mod == "bill":
            BillingModule(self.main_view, db).render()
        elif mod == "inv":
            InventoryModule(self.main_view, db).render()
        elif mod == "rep":
            ReportsModule(self.main_view, db).render()
        elif mod == "usr":
            UserManagementModule(self.main_view, db).render()

    def logout(self):
        self.destroy()
        main()

def main():
    # Success callback creates the App and starts its mainloop
    login = LoginWindow(lambda u, r: CrackerApp(u, r).mainloop())
    login.mainloop()

if __name__ == "__main__":
    main()