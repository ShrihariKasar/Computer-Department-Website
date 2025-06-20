# 🏆 College Achievements Portal

A Flask-based web application designed to showcase and manage achievements of students and staff at Matoshri College of Engineering.

---

## 📌 Features

- 🎓 Display approved achievements on the home page
- 🧾 Admin dashboard to approve, reject, delete entries
- 📁 Upload certificates and display as image cards
- 🌐 Responsive UI with Bootstrap 5
- ✅ Export all approved achievements to Excel
- 🔒 Admin login system with hashed passwords

---

## 🖼️ Screenshots

| Home Page | Admin Dashboard |
|-----------|-----------------|
| ![Home](https://github.com/ShrihariKasar/Student-Achievement-Portal/blob/main/home.png) | ![Admin](https://github.com/ShrihariKasar/Student-Achievement-Portal/blob/main/admin.png) |

---

## 🔧 Tech Stack

- **Frontend:** HTML, CSS, Bootstrap 5, Jinja2
- **Backend:** Flask (Python)
- **Database:** MySQL
- **Libraries:** Pandas, OpenPyXL, Werkzeug

---

## 🚀 Installation

### 1. Clone the repo

```bash
git clone https://github.com/ShrihariKasar/Student-Achievement-Portal.git
cd college-achievements-portal
````

### 2. Set up virtual environment

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate (Windows)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure `.env` or `config.py`

Update your database configuration and upload folder path in `config.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'youruser',
    'password': 'yourpass',
    'database': 'achievements_db'
}

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
```

### 5. Set up MySQL

```sql
CREATE DATABASE achievements_db;

USE achievements_db;

CREATE TABLE achievements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_name VARCHAR(255),
  activity_details TEXT,
  organized_by VARCHAR(255),
  activity_date DATE,
  remark TEXT,
  certificate VARCHAR(255),
  status VARCHAR(20),
  display_on_home BOOLEAN DEFAULT 0
);
```

### 6. Run the app

```bash
python app.py
```

---

## 👨‍💻 Contributors

* **Shrihari Kasar** – [@shriharikasar](https://github.com/shriharikasar)
* **Ishwari Gamne**
* **Utkarsha Kakulte**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙌 Support

If you find this project useful, give it a ⭐️ and feel free to contribute or raise issues!

