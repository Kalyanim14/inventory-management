# MySQL-based Inventory Management System using Tkinter

import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import mysql.connector

# Establish MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sharvan8",
    database="inventory_system"
)
cursor = db.cursor(dictionary=True)

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System")
        self.root.geometry("800x600")  # Enhanced window size
        self.root.configure(bg="white")
        self.current_user = None
        self.current_org_id = None
        self.current_org_name = None
        self.login_screen()

    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def login_screen(self):
        self.clear_frame()

        self.login_frame = tk.Frame(self.root, padx=40, pady=40, bg="white")
        self.login_frame.pack(expand=True)

        tk.Label(self.login_frame, text="Organization:", font=("Arial", 12), bg="white").grid(row=0, column=0, pady=10, sticky="e")
        self.org_entry = tk.Entry(self.login_frame, width=30)
        self.org_entry.grid(row=0, column=1, pady=10)

        tk.Label(self.login_frame, text="Username:", font=("Arial", 12), bg="white").grid(row=1, column=0, pady=10, sticky="e")
        self.username_entry = tk.Entry(self.login_frame, width=30)
        self.username_entry.grid(row=1, column=1, pady=10)

        tk.Label(self.login_frame, text="Password:", font=("Arial", 12), bg="white").grid(row=2, column=0, pady=10, sticky="e")
        self.password_entry = tk.Entry(self.login_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, pady=10)

        tk.Button(self.login_frame, text="Login", command=self.login, width=20, bg="#90EE90").grid(row=3, columnspan=2, pady=10)
        tk.Button(self.login_frame, text="Register", command=self.register, width=20, bg="#ADD8E6").grid(row=4, columnspan=2, pady=5)

    def login(self):
        org = self.org_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            cursor.execute("""
                SELECT u.*, o.id as org_id, o.name as org_name FROM users u
                JOIN organizations o ON u.org_id = o.id
                WHERE o.name = %s AND u.username = %s
            """, (org, username))
            user = cursor.fetchone()

            if user and user["password"] == password:
                if not user["approved"] and user["designation"] != "admin":
                    messagebox.showerror("Login Failed", "Admin approval required.")
                    return
                self.current_user = user["username"]
                self.current_org_id = user["org_id"]
                self.current_org_name = user["org_name"]
                self.dashboard(user["designation"])
            else:
                messagebox.showerror("Login Failed", "Incorrect credentials.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def register(self):
        try:
            org = simpledialog.askstring("Register", "Enter organization name:")
            username = simpledialog.askstring("Register", "Enter username:")
            password = simpledialog.askstring("Register", "Enter password:")

            if not org or not username or not password:
                messagebox.showerror("Register", "All fields are required.")
                return

            cursor.execute("SELECT id FROM organizations WHERE name = %s", (org,))
            org_row = cursor.fetchone()

            if org_row:
                org_id = org_row["id"]
                designation = "employee"
                approved = False
            else:
                cursor.execute("INSERT INTO organizations (name) VALUES (%s)", (org,))
                db.commit()
                org_id = cursor.lastrowid
                designation = "admin"
                approved = True

            cursor.execute("SELECT * FROM users WHERE username = %s AND org_id = %s", (username, org_id))
            if cursor.fetchone():
                messagebox.showerror("Register", "Username already exists.")
                return

            cursor.execute("""
                INSERT INTO users (org_id, username, password, designation, approved)
                VALUES (%s, %s, %s, %s, %s)
            """, (org_id, username, password, designation, approved))
            db.commit()

            messagebox.showinfo("Register", "Registration successful.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def dashboard(self, designation):
        self.clear_frame()
        header = tk.Label(self.root, text=f"{self.current_org_name} | {self.current_user} ({designation})", bg="lightblue", font=("Arial", 14, "bold"))
        header.pack(fill=tk.X, pady=10)

        dashboard_frame = tk.Frame(self.root, padx=20, pady=20, bg="white")
        dashboard_frame.pack(expand=True, fill=tk.BOTH)

        button_conf = {"fill": tk.X, "padx": 10, "pady": 5}

        tk.Button(dashboard_frame, text="Add Item", command=self.add_item, height=2).pack(**button_conf)
        tk.Button(dashboard_frame, text="View Inventory", command=self.view_inventory, height=2).pack(**button_conf)
        tk.Button(dashboard_frame, text="Edit Item", command=self.edit_item, height=2).pack(**button_conf)
        tk.Button(dashboard_frame, text="Delete Item", command=self.delete_item, height=2).pack(**button_conf)

        if designation == "admin":
            tk.Button(dashboard_frame, text="Approve Users", command=self.approve_users, height=2, bg="#DDEEFF").pack(**button_conf)

        tk.Button(dashboard_frame, text="Logout", command=self.login_screen, height=2, bg="#FFCCCC").pack(**button_conf)

    def view_inventory(self):
        try:
            cursor.execute(
                "SELECT name, qty, price, last_updated_by, last_updated_on FROM inventory WHERE org_id = %s",
                (self.current_org_id,)
            )
            items = cursor.fetchall()

            if not items:
                messagebox.showinfo("Inventory", "No items found.")
                return

            view_win = tk.Toplevel(self.root)
            view_win.title("Inventory List")
            view_win.geometry("700x500")
            text_area = tk.Text(view_win, wrap="word", font=("Courier New", 10))
            text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

            for item in items:
                name = item['name'] if item['name'] is not None else 'N/A'
                qty = item['qty'] if item['qty'] is not None else 0
                price = item['price'] if item['price'] is not None else 0.0
                updated_by = item['last_updated_by'] if item['last_updated_by'] is not None else 'N/A'
                updated_on = item['last_updated_on'] if item['last_updated_on'] is not None else 'N/A'

                entry = (
                    f"Name: {name}, Qty: {qty}, Price: ₹{price:.2f}, "
                    f"Updated By: {updated_by}, On: {updated_on}\n"
                )
                text_area.insert(tk.END, entry + "\n")

            text_area.config(state=tk.DISABLED)

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def add_item(self):
        try:
            name = simpledialog.askstring("Add Item", "Enter item name:")
            if not name:
                return
            qty = simpledialog.askinteger("Add Item", f"Enter quantity for '{name}':")
            if qty is None:
                return
            price = simpledialog.askfloat("Add Item", f"Enter price for '{name}':")
            if price is None:
                return

            # Check for duplicate item name within the same organization
            cursor.execute(
                "SELECT id FROM inventory WHERE org_id = %s AND name = %s",
                (self.current_org_id, name)
            )
            existing = cursor.fetchone()
            if existing:
                messagebox.showwarning("Duplicate Item", f"Item '{name}' already exists in inventory.")
                return

            cursor.execute("""
                INSERT INTO inventory (org_id, name, qty, price, last_updated_by, last_updated_on)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (self.current_org_id, name, qty, price, self.current_user, datetime.now()))
            db.commit()
            messagebox.showinfo("Success", f"Item '{name}' added.")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))


    def edit_item(self):
        try:
            cursor.execute("SELECT id, name FROM inventory WHERE org_id = %s", (self.current_org_id,))
            items = cursor.fetchall()
            if not items:
                messagebox.showinfo("Edit Item", "No items found.")
                return

            item_dict = {str(i+1): item for i, item in enumerate(items)}
            item_list_str = "\n".join([f"{i}: {item['name']}" for i, item in item_dict.items()])
            choice = simpledialog.askstring("Edit Item", f"Select item to edit:\n{item_list_str}")
            if choice not in item_dict:
                return

            selected = item_dict[choice]
            new_qty = simpledialog.askinteger("Edit Quantity", f"New quantity for '{selected['name']}':")
            new_price = simpledialog.askfloat("Edit Price", f"New price for '{selected['name']}':")

            cursor.execute("""
                UPDATE inventory SET qty = %s, price = %s, last_updated_by = %s, last_updated_on = %s
                WHERE id = %s
            """, (new_qty, new_price, self.current_user, datetime.now(), selected['id']))
            db.commit()
            messagebox.showinfo("Success", "Item updated.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def delete_item(self):
        try:
            cursor.execute("SELECT id, name FROM inventory WHERE org_id = %s", (self.current_org_id,))
            items = cursor.fetchall()
            if not items:
                messagebox.showinfo("Delete Item", "No items found.")
                return

            item_dict = {str(i+1): item for i, item in enumerate(items)}
            item_list_str = "\n".join([f"{i}: {item['name']}" for i, item in item_dict.items()])
            choice = simpledialog.askstring("Delete Item", f"Select item to delete:\n{item_list_str}")
            if choice not in item_dict:
                return

            selected = item_dict[choice]
            cursor.execute("DELETE FROM inventory WHERE id = %s", (selected['id'],))
            db.commit()
            messagebox.showinfo("Success", f"Item '{selected['name']}' deleted.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

    def approve_users(self):
        try:
            cursor.execute("SELECT id, username FROM users WHERE org_id = %s AND approved = 0", (self.current_org_id,))
            pending = cursor.fetchall()
            if not pending:
                messagebox.showinfo("Approve Users", "No users pending approval.")
                return

            for user in pending:
                confirm = messagebox.askyesno("Approve User", f"Approve user: {user['username']}?")
                if confirm:
                    cursor.execute("UPDATE users SET approved = 1 WHERE id = %s", (user['id'],))
            db.commit()
            messagebox.showinfo("Done", "All approvals complete.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
