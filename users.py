import customtkinter as ctk
from tkinter import messagebox, ttk

class UserManagementModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        for widget in self.main_view.winfo_children(): widget.destroy()

        ctk.CTkLabel(self.main_view, text="User Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        # Input Frame
        entry_frame = ctk.CTkFrame(self.main_view)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        self.username_in = ctk.CTkEntry(entry_frame, placeholder_text="Username", width=150)
        self.username_in.grid(row=0, column=0, padx=5, pady=10)
        
        self.password_in = ctk.CTkEntry(entry_frame, placeholder_text="Password", show="*", width=150)
        self.password_in.grid(row=0, column=1, padx=5)
        
        self.role_in = ctk.CTkComboBox(entry_frame, values=["Staff", "Admin"], width=100)
        self.role_in.grid(row=0, column=2, padx=5)
        
        ctk.CTkButton(entry_frame, text="Add User", fg_color="#2ecc71", command=self.add_user).grid(row=0, column=3, padx=5)

        # User List
        self.tree = ttk.Treeview(self.main_view, columns=("ID", "User", "Role"), show='headings')
        self.tree.heading("ID", text="ID"); self.tree.heading("User", text="Username"); self.tree.heading("Role", text="Role")
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_users()

    def add_user(self):
        u, p, r = self.username_in.get(), self.password_in.get(), self.role_in.get()
        if not (u and p): return
        try:
            self.db.cursor.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)", (u, p, r))
            self.db.conn.commit()
            self.refresh_users()
            messagebox.showinfo("Success", f"User {u} added.")
        except:
            messagebox.showerror("Error", "Username already exists.")

    def refresh_users(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute("SELECT id, username, role FROM users")
        for row in self.db.cursor.fetchall(): self.tree.insert("", "end", values=row)