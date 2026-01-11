import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import csv
import logging
from datetime import datetime

class UserManagementModule:
    def __init__(self, main_view, db):
        self.main_view = main_view
        self.db = db

    def render(self):
        """Displays the User Management UI"""
        for widget in self.main_view.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.main_view, text="User Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Entry Form ---
        f = ctk.CTkFrame(self.main_view)
        f.pack(fill="x", padx=20, pady=10)
        
        self.u_name = ctk.CTkEntry(f, placeholder_text="Username", width=150)
        self.u_name.grid(row=0, column=0, padx=5, pady=10)
        
        self.u_pass = ctk.CTkEntry(f, placeholder_text="Password", show="*", width=150)
        self.u_pass.grid(row=0, column=1, padx=5)

        self.u_role = ctk.CTkComboBox(f, values=["Admin", "Staff"], width=120)
        self.u_role.set("Staff") # Default
        self.u_role.grid(row=0, column=2, padx=5)
        
        # Action Buttons
        ctk.CTkButton(f, text="Save/Update", width=100, command=self.save_user).grid(row=0, column=3, padx=5)
        ctk.CTkButton(f, text="Clear", width=80, fg_color="grey", command=self.clear_entries).grid(row=0, column=4, padx=5)

        # --- Bulk & Action Buttons ---
        btn_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        btn_f.pack(fill="x", padx=20)
        
        ctk.CTkButton(btn_f, text="📤 Export Users CSV", fg_color="#27ae60", command=self.export_users).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="🗑️ Delete User", fg_color="#e74c3c", command=self.delete_user).pack(side="right", padx=5)

        # --- Table ---
        cols = ("Username", "Role")
        self.tree = ttk.Treeview(self.main_view, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200, anchor="center")
        
        # Selection event for modifying
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh_list()

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        vals = self.tree.item(selected[0])['values']
        
        self.u_name.delete(0, 'end')
        self.u_name.insert(0, vals[0])
        self.u_role.set(vals[1])
        # Note: Password is not fetched for security; re-entry required for update

    def save_user(self):
        u, p, r = self.u_name.get(), self.u_pass.get(), self.u_role.get()
        if not u or not p:
            messagebox.showwarning("Input Error", "Username and Password are required")
            return

        try:
            # Upsert Logic: If username exists, update password and role
            self.db.cursor.execute("""
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
                ON CONFLICT(username) 
                DO UPDATE SET password=excluded.password, role=excluded.role
            """, (u, p, r))
            
            self.db.conn.commit()
            logging.info(f"USER UPDATE: {u} assigned as {r}")
            messagebox.showinfo("Success", f"User {u} saved/updated.")
            self.refresh_list()
            self.clear_entries()
        except Exception as e:
            logging.error(f"USER SAVE FAILED: {str(e)}")

    def delete_user(self):
        selected = self.tree.selection()
        if not selected: return
        u = self.tree.item(selected[0])['values'][0]
        
        if u == "admin": # Guard against deleting the primary admin
            messagebox.showerror("Error", "Primary admin cannot be deleted.")
            return

        if messagebox.askyesno("Confirm", f"Delete user '{u}'?"):
            self.db.cursor.execute("DELETE FROM users WHERE username=?", (u,))
            self.db.conn.commit()
            logging.warning(f"USER DELETED: {u}")
            self.refresh_list()

    def export_users(self):
        self.db.cursor.execute("SELECT username, role FROM users")
        rows = self.db.cursor.fetchall()
        
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"User_List_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if not path: return

        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Username", "Role"])
                writer.writerows(rows)
            messagebox.showinfo("Success", f"User list exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

    def refresh_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute("SELECT username, role FROM users")
        for row in self.db.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def clear_entries(self):
        self.u_name.delete(0, 'end')
        self.u_pass.delete(0, 'end')
        self.u_role.set("Staff")