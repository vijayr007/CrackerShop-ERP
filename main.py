import customtkinter as ctk
from database import db
from inventory import InventoryModule
from billing import BillingModule
from reports import ReportsModule
from tkinter import messagebox

class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.title("Login")
        self.geometry("400x350")
        self.on_success = on_success

        ctk.CTkLabel(self, text="CrackerShop ERP", font=("Arial", 24, "bold")).pack(pady=20)
        self.u_in = ctk.CTkEntry(self, placeholder_text="Username", width=200)
        self.u_in.pack(pady=10)
        self.p_in = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=200)
        self.p_in.pack(pady=10)
        ctk.CTkButton(self, text="Login", command=self.login).pack(pady=20)

    def login(self):
        # FIX: Get data BEFORE destroying widgets
        u, p = self.u_in.get(), self.p_in.get()
        db.cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
        res = db.cursor.fetchone()
        if res:
            role = res[0]
            self.destroy() # Now it is safe to destroy
            self.on_success(u, role)
        else:
            messagebox.showerror("Error", "Invalid Credentials")

class CrackerApp(ctk.CTk):
    def __init__(self, user, role):
        super().__init__()
        self.title(f"CrackerShop - {user}")
        self.geometry("1100x700")
        self.role = role

        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.main_view = ctk.CTkFrame(self)
        self.main_view.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkButton(self.sidebar, text="💳 Billing", command=lambda: self.load_module("bill")).pack(fill="x", padx=10, pady=5)
        
        if self.role == "Admin":
            ctk.CTkButton(self.sidebar, text="📦 Inventory", command=lambda: self.load_module("inv")).pack(fill="x", padx=10, pady=5)
            ctk.CTkButton(self.sidebar, text="📊 Reports", command=lambda: self.load_module("rep")).pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(self.sidebar, text="Logout", fg_color="red", command=self.logout).pack(side="bottom", pady=20)
        self.load_module("bill")

    def load_module(self, mod):
        for w in self.main_view.winfo_children(): w.destroy()
        if mod == "bill": BillingModule(self.main_view, db).render()
        elif mod == "inv": InventoryModule(self.main_view, db).render()
        elif mod == "rep": ReportsModule(self.main_view, db).render()

    def logout(self):
        self.destroy()
        main()

def main():
    app = LoginWindow(lambda u, r: CrackerApp(u, r).mainloop())
    app.mainloop()

if __name__ == "__main__":
    main()