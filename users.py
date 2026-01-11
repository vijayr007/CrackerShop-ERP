import customtkinter as ctk
from tkinter import messagebox, ttk

class UserManagementModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        # Clear the frame
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="User Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        # Input Section
        entry_frame = ctk.CTkFrame(self.main_view)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        self.u_name = ctk.CTkEntry(entry_frame, placeholder_text="Username", width=150)
        self.u_name.grid(row=0, column=0, padx=5, pady=10)
        
        self.u_pass = ctk.CTkEntry(entry_frame, placeholder_text="Password", show="*", width=150)
        self.u_pass.grid(row=0, column=1, padx=5)
        
        self.u_role = ctk.CTkComboBox(entry_frame, values=["Staff", "Admin"], width=100)
        self.u_role.grid(row=0, column=2, padx=5)
        self.u_role.set("Staff")
        
        ctk.CTkButton(entry_frame, text="Add User", fg_color="#2ecc71", command=self.add_user).grid(row=0, column=3, padx=5)

        # User Table
        columns = ("ID", "Username", "Role")
        self.tree = ttk.Treeview(self.main_view, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_list()

    def add_user(self):
        u, p, r = self.u_name.get(), self.u_pass.get(), self.u_role.get()
        if not (u and p):
            messagebox.showwarning("Input Error", "All fields are required")
            return
        
        try:
            self.db.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (u, p, r))
            self.db.conn.commit()
            messagebox.showinfo("Success", f"User {u} added successfully")
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Error", "Username already exists")

    def refresh_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute("SELECT id, username, role FROM users")
        for row in self.db.cursor.fetchall():
            self.tree.insert("", "end", values=row)