# 🌐 Computer Department Website  

A Flask-based web application for the **Computer Department at Matoshri College of Engineering**, integrating achievements, events, announcements, study materials, Dev Club, and more — with a responsive, modern design and role-based content management.  

---

## 📌 Features  

- 🏆 **Achievements Portal** – Showcase approved student & faculty accomplishments  
- 🧾 **Admin Dashboard** – Approve, reject, or delete entries (achievements, projects, users, notices)  
- 📁 **File Uploads** – Certificates, study materials, notices, and attendance sheets  
- 🎓 **Role-Based Access** – Separate dashboards for students, staff, and admin  
- 📑 **Announcements & Notices** – Upload/view exam schedules, holiday notices (PDFs/images)  
- 📚 **Study Materials** – Organized by class & subject, with staff upload & delete option  
- 📊 **Attendance Management** – Staff upload via Excel, students view in popup  
- 💻 **Dev Club Page** – Highlight projects, coordinators, and student submissions  
- 🎉 **Events Section** – Showcase department activities & event highlights  
- 🌐 **Responsive UI** – Built with Bootstrap 5, optimized for desktop & mobile  
- ✅ **Data Export** – Export approved achievements/projects to Excel  
- 🔒 **Secure Auth** – Hashed passwords, login & session-based role handling  

---

## 🖼️ Screenshots  

| Home Page | Admin Dashboard | Dev Club Page | Notices Section |
|-----------|----------------|---------------|----------------|
| ![Home](https://github.com/ShrihariKasar/Student-Achievement-Portal/blob/main/home.png) | ![Admin](https://github.com/ShrihariKasar/Student-Achievement-Portal/blob/main/admin.png) | ![Dev Club](https://github.com/ShrihariKasar/Student-Achievement-Portal/blob/main/devclub.png) | ![Notices](https://github.com/ShrihariKasar/Student-Achievement-Portal/blob/main/notices.png) |  

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
git clone https://github.com/ShrihariKasar/Computer-Department-Website.git
cd computer-department-website
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

Update your database configuration and upload folder paths:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'youruser',
    'password': 'yourpass',
    'database': 'compdept_db'
}

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'xlsx'}
```

### 5. Set up MySQL

```sql
CREATE DATABASE compdept_db;
```

*(Tables for achievements, users, study\_materials, attendance, announcements, projects, coordinators, etc. are included in `schema.sql`)*

### 6. Run the app

```bash
python app.py
```

---

## 👨‍💻 Contributors

* **Shrihari Kasar** – [@shriharikasar](https://github.com/shriharikasar)
* **Utkarsha Kakulte**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙌 Support

If you find this project useful, give it a ⭐️ and feel free to contribute or raise issues!

```

Do you also want me to **generate the `schema.sql` file in `.md` format** so it can be directly linked in the README?
```
