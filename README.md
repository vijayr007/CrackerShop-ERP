🧨 CrackerShop ERP v2.0
A modern, modular Point of Sale (POS) and Inventory Management System designed specifically for firework retailers. Built with Python and CustomTkinter, this application provides a sleek dark-mode interface with local database persistence.

✨ Features
Modular Architecture: Organized into separate files for Database, Inventory, Billing, and Reports.

SKU/Product Code Support: Every item has a unique code for fast lookup.

Dynamic Billing: A real-time shopping cart system that allows you to add, search, and cancel items before finalizing a sale.

Inventory Control: Automated stock deduction upon sale completion and manual stock entry.

Sales Reporting: Track total revenue and view transaction history.

Database Persistence: Powered by SQLite3 (no external server required).

📂 Project Structure
Plaintext

cracker_shop/
├── main.py              # Entry point & Navigation
├── database.py          # SQLite schema & connection
├── inventory.py         # Stock management module
├── billing.py           # POS & Cart logic
├── reports.py           # Sales analytics module
└── cracker_shop.db      # Local database (auto-generated)
🚀 Getting Started
Prerequisites
Python 3.8 or higher

Required Libraries:

Bash

pip install customtkinter pandas
Installation
Clone the repository or download the source code.

Navigate to the project folder.

Run the application:

Bash

python main.py
🖥️ Usage Guide
Login: Use the default credentials (Admin / admin123).

Add Stock: Go to the Inventory tab to enter your products with unique codes.

Create a Bill: In the Billing tab, search for a product by its code or name, enter the quantity, and add it to the cart.

Checkout: Click Complete Sale & Print. This will deduct stock and save the transaction.

View Sales: Check the Reports tab to see your total revenue.

🛠️ Building the Executable
To create a standalone Windows .exe file:

Install PyInstaller: pip install pyinstaller

Run the build command:

Bash

pyinstaller --noconsole --onefile --name "CrackerShop_Pro" main.py