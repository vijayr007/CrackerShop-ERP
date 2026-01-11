import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import csv, logging, os

class CategoryModule:
    def __init__(self, main_view, db):
        self.main_view, self.db = main_view, db

    def render(self):
        for w in self.main_view.winfo_children(): w.destroy()
        
        ctk.CTkLabel(self.main_view, text="Category Management", font=("Arial", 22, "bold")).pack(pady=10)
        
        # --- Entry Form ---
        f = ctk.CTkFrame(self.main_view)
        f.pack(fill="x", padx=20, pady=10)
        
        self.c_code = ctk.CTkEntry(f, placeholder_text="Cat Code (e.g. RKT)", width=120)
        self.c_code.grid(row=0, column=0, padx=5, pady=10)
        self.c_name = ctk.CTkEntry(f, placeholder_text="Category Name", width=150)
        self.c_name.grid(row=0, column=1, padx=5)
        self.c_desc = ctk.CTkEntry(f, placeholder_text="Description", width=200)
        self.c_desc.grid(row=0, column=2, padx=5)
        
        ctk.CTkButton(f, text="Save/Update", width=100, command=self.save_category).grid(row=0, column=3, padx=5)

        # --- Utility Buttons ---
        util_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        util_f.pack(fill="x", padx=20)
        
        ctk.CTkButton(util_f, text="📥 Import CSV", fg_color="#3498db", width=120, command=self.import_csv).pack(side="left", padx=5)
        ctk.CTkButton(util_f, text="📤 Export CSV", fg_color="#3498db", width=120, command=self.export_csv).pack(side="left", padx=5)
        ctk.CTkButton(util_f, text="🗑️ Delete Selected", fg_color="#e74c3c", width=120, command=self.delete_category).pack(side="right", padx=5)

        # --- Table ---
        cols = ("Code", "Name", "Description")
        self.tree = ttk.Treeview(self.main_view, columns=cols, show='headings')
        for c in cols: 
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.refresh()

    def save_category(self):
        code, name, desc = self.c_code.get().upper(), self.c_name.get(), self.c_desc.get()
        if not (code and name):
            return messagebox.showwarning("Error", "Code and Name required")
        
        try:
            self.db.cursor.execute("""
                INSERT INTO categories (cat_code, name, description) VALUES (?, ?, ?)
                ON CONFLICT(cat_code) DO UPDATE SET name=excluded.name, description=excluded.description
            """, (code, name, desc))
            self.db.conn.commit()
            logging.info(f"CATEGORY SAVED: {code} - {name}")
            self.refresh()
            self.c_code.delete(0, 'end'); self.c_name.delete(0, 'end'); self.c_desc.delete(0, 'end')
        except Exception as e:
            logging.error(f"CAT SAVE ERROR: {str(e)}")

    def delete_category(self):
        sel = self.tree.selection()
        if not sel: return
        code = self.tree.item(sel[0])['values'][0]
        
        if messagebox.askyesno("Confirm", f"Delete category {code}? Items in inventory with this category will remain."):
            self.db.cursor.execute("DELETE FROM categories WHERE cat_code=?", (code,))
            self.db.conn.commit()
            logging.warning(f"CATEGORY DELETED: {code}")
            self.refresh()

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.db.cursor.execute("SELECT cat_code, name, description FROM categories")
        for r in self.db.cursor.fetchall(): self.tree.insert("", "end", values=r)

    def export_csv(self):
        if not os.path.exists("exports"): os.makedirs("exports")
        path = "exports/categories_backup.csv"
        self.db.cursor.execute("SELECT cat_code, name, description FROM categories")
        data = self.db.cursor.fetchall()
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["cat_code", "name", "description"])
            writer.writerows(data)
        messagebox.showinfo("Success", f"Exported to {path}")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        try:
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.db.cursor.execute("INSERT INTO categories (cat_code, name, description) VALUES (?,?,?) ON CONFLICT(cat_code) DO UPDATE SET name=excluded.name", (r['cat_code'], r['name'], r['description']))
            self.db.conn.commit()
            logging.info(f"CATEGORIES IMPORTED from {path}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", "Required headers: cat_code, name, description")