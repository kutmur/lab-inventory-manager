# Lab Inventory Management System

A Python-based inventory management system for university laboratories. Designed for managing, tracking, and exporting lab inventories across multiple labs, with full user login, role control, and logging support.

---

## 🚀 Features

- ✅ Add, edit, delete, and transfer inventory items between labs
- 🔐 User login system with **role-based access** (Admin / User)
- 📂 Persistent data storage using JSON
- ✍️ Full action logging per user (`user_log.json`)
- 🔎 Live search by product name or registry number
- 📄 Export to Excel, PDF, and Word formats
- 📊 Built-in GUI log viewer
- 🧼 Organized export folders (`exports/pdf`, `exports/word`, etc.)

---

## 👤 User Roles

| Role   | Permissions                                    |
|--------|------------------------------------------------|
| Admin  | Full control (add/edit/delete/export/transfer) |
| User   | Restricted (view + add only)                   |

User credentials are stored in `users.json`. You can define roles and passwords there.

---

## 📂 Directory Structure

```
lab-inventory-manager/
├── main.py
├── inventory.json
├── transfer_log.json
├── user_log.json
├── users.json
├── requirements.txt
├── README.md
└── exports/
    ├── pdf/
    ├── word/
    └── excel/
```

---

## 🧪 Requirements

Python 3.8+

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

```bash
python main.py
```

Login using credentials from `users.json`.

---

## ✍️ Future Plans

- 🌐 Web version (Flask/Django or React + FastAPI)
- 🧠 Transfer history viewer
- 🧹 QR code support for inventory items
- 📜 Report generation with custom templates
- 🔐 Password hashing with bcrypt

---

## 👤 Author

Developed by [Halil İbrahim Kutmur](https://github.com/EXPERT2007)  
Student at Bursa Technical University | AI & Software Dev 🧠💻

---

## 📄 License

MIT License
