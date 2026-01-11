# Fireworks ERP - CrackerShop Management System

A professional Inventory, Billing, and User Management system built with Python and CustomTkinter. Designed specifically for retail shops requiring real-time stock tracking and sales reporting.



## 🚀 Features

- **Dynamic Billing Terminal**: 
    - Partial search for products (search by name or code).
    - Category-based filtering.
    - Live stock validation (prevents over-selling based on cart contents).
- **Inventory Management**: 
    - Full CRUD (Add/Update/Delete) for products.
    - Bulk data handling via **CSV Import/Export**.
- **Advanced Reporting**: 
    - Filter sales by Bill ID, Category, or Date Range.
    - Generate professional **PDF Reports** with automatic table formatting.
    - Export filtered data to CSV.
- **User Management**: 
    - Role-based access control (Admin vs. Staff).
    - Secure user creation and modification.
- **Database**: 
    - Local SQLite implementation for speed and reliability.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/yourusername/crackershop-erp.git](https://github.com/yourusername/crackershop-erp.git)
   cd crackershop-erp

reate a Virtual Environment:

Bash

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install Dependencies:

Bash

pip install -r requirements.txt
Initialize Database: The system will automatically create crackershop.db on the first run. Ensure database.py is present.

📁 Project Structure
Plaintext

├── main.py              # Application entry point & Login logic
├── database.py          # SQLite connection and schema setup
├── billing.py           # POS / Billing Terminal logic
├── inventory.py         # Stock management & CSV handling
├── categories.py        # Category management
├── reports.py           # Sales analysis & PDF generation
├── users.py             # User accounts & Role management
├── exports/             # Generated PDFs & CSVs (Git Ignored)
├── .gitignore           # Files excluded from Version Control
└── requirements.txt     # List of Python dependencies
📖 Usage
Login: Use the default admin credentials (configured in your database).

Setup: Go to Categories to define your product types (e.g., Rockets, Sparklers).

Inventory: Use Import CSV to quickly load your stock or add items manually.

Billing: Search for items in the Billing tab. The system will show you "Effective Available Stock" (Total Stock minus what's currently in your cart).

Reports: Use the Reports tab to view revenue and export PDFs for your records.

📝 Important Notes
Exports: All generated reports are saved in the exports/ folder. This folder is ignored by Git to keep the repo clean.

Logs: System errors and transaction logs are saved in app.log.   