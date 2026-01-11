import customtkinter as ctk

from tkinter import messagebox, ttk, filedialog

import csv

import logging

from datetime import datetime

class CustomerModule:

    def __init__(self, main_view, db):

        self.main_view = main_view

        self.db = db

    def render(self):

        """Displays the Customer Management UI"""

        for widget in self.main_view.winfo_children():

            widget.destroy()

        ctk.CTkLabel(self.main_view, text="Customer Directory (CRM)", font=("Arial", 22, "bold")).pack(pady=10)

        

        # --- Entry Form ---

        f = ctk.CTkFrame(self.main_view)

        f.pack(fill="x", padx=20, pady=10)

        

        self.phone = ctk.CTkEntry(f, placeholder_text="Phone Number (Primary Key)", width=180)

        self.phone.grid(row=0, column=0, padx=5, pady=10)

        

        self.name = ctk.CTkEntry(f, placeholder_text="Customer Name", width=180)

        self.name.grid(row=0, column=1, padx=5)

        self.address = ctk.CTkEntry(f, placeholder_text="Full Address", width=300)

        self.address.grid(row=0, column=2, padx=5)

        

        # Action Buttons

        btn_f = ctk.CTkFrame(f, fg_color="transparent")

        btn_f.grid(row=0, column=3, padx=10)

        

        ctk.CTkButton(btn_f, text="Save/Update", width=100, command=self.save_customer).grid(row=0, column=0, padx=2)

        ctk.CTkButton(btn_f, text="Clear", width=60, fg_color="grey", command=self.clear_entries).grid(row=0, column=1, padx=2)

        # --- Bulk Actions ---

        action_bar = ctk.CTkFrame(self.main_view, fg_color="transparent")

        action_bar.pack(fill="x", padx=20)

        

        ctk.CTkButton(action_bar, text="📤 Export CSV", fg_color="#27ae60", command=self.export_customers).pack(side="left", padx=5)

        ctk.CTkButton(action_bar, text="🗑️ Delete Selected", fg_color="#e74c3c", command=self.delete_customer).pack(side="right", padx=5)

        # --- Table ---

        cols = ("Phone", "Name", "Address")

        self.tree = ttk.Treeview(self.main_view, columns=cols, show='headings')

        for col in cols:

            self.tree.heading(col, text=col)

            self.tree.column(col, width=200, anchor="w")

        

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

        

        self.refresh_list()

    def on_row_select(self, event):

        selected = self.tree.selection()

        if not selected: return

        vals = self.tree.item(selected[0])['values']

        

        self.clear_entries()

        self.phone.insert(0, vals[0])

        self.name.insert(0, vals[1])

        self.address.insert(0, vals[2])

    def save_customer(self):

        p, n, a = self.phone.get().strip(), self.name.get().strip(), self.address.get().strip()

        if not p or not n:

            messagebox.showwarning("Input Error", "Phone and Name are mandatory.")

            return

        try:

            # UPSERT logic: Insert or Update if phone exists

            self.db.cursor.execute("""

                INSERT INTO customers (phone, name, address) 

                VALUES (?, ?, ?)

                ON CONFLICT(phone) 

                DO UPDATE SET name=excluded.name, address=excluded.address

            """, (p, n, a))

            

            self.db.conn.commit()

            messagebox.showinfo("Success", f"Customer {n} saved.")

            self.refresh_list()

            self.clear_entries()

        except Exception as e:

            logging.error(f"CUSTOMER SAVE FAILED: {str(e)}")

            messagebox.showerror("Error", f"Failed to save: {e}")

    def delete_customer(self):

        selected = self.tree.selection()

        if not selected:

            messagebox.showwarning("Select", "Please select a customer from the list to delete.")

            return

            

        p = self.tree.item(selected[0])['values'][0]

        n = self.tree.item(selected[0])['values'][1]

        if messagebox.askyesno("Confirm", f"Are you sure you want to delete customer '{n}' ({p})?"):

            try:

                self.db.cursor.execute("DELETE FROM customers WHERE phone=?", (p,))

                self.db.conn.commit()

                self.refresh_list()

                self.clear_entries()

            except Exception as e:

                messagebox.showerror("Error", f"Delete failed: {e}")

    def export_customers(self):

        self.db.cursor.execute("SELECT phone, name, address FROM customers")

        rows = self.db.cursor.fetchall()

        

        if not rows:

            messagebox.showinfo("Empty", "No customer data to export.")

            return

        path = filedialog.asksaveasfilename(

            defaultextension=".csv",

            filetypes=[("CSV Files", "*.csv")],

            initialfile=f"Customer_List_{datetime.now().strftime('%Y%m%d')}.csv"

        )

        if not path: return

        try:

            with open(path, 'w', newline='', encoding='utf-8') as f:

                writer = csv.writer(f)

                writer.writerow(["Phone", "Name", "Address"])

                writer.writerows(rows)

            messagebox.showinfo("Success", f"Customer directory exported to {path}")

        except Exception as e:

            messagebox.showerror("Error", f"Export failed: {e}")

    def refresh_list(self):

        for i in self.tree.get_children(): self.tree.delete(i)

        self.db.cursor.execute("SELECT phone, name, address FROM customers ORDER BY name ASC")

        for row in self.db.cursor.fetchall():

            self.tree.insert("", "end", values=row)

    def clear_entries(self):

        self.phone.delete(0, 'end')

        self.name.delete(0, 'end')

        self.address.delete(0, 'end')