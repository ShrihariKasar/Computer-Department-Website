from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
import os
import time
import pandas as pd
from io import BytesIO
from models import Event  # If you have a models.py file
from flask import send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_CONFIG, UPLOAD_FOLDER, ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv('SECRET_KEY', '3ed2e95f933aeaa2d2b21267496eac8f')

ADMIN_USERNAME = os.getenv('ADMIN_ID', 'ShradhaShinde')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASS_HASH') or generate_password_hash('SS@mcoerc#304')

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_session():
    return dict(session=session)

# ----------------- MAIN PAGES -----------------

@app.route('/')
def department_home():
    return render_template('department_home.html')

@app.route('/index')
def index():
    year = request.args.get('year')
    sort = request.args.get('sort', 'desc')  # Default to newest first

    db = connect_db()
    cursor = db.cursor(dictionary=True)

    # Build query with optional filters
    query = "SELECT * FROM achievements WHERE status = 'approved'"
    params = []

    if year:
        query += " AND YEAR(activity_date) = %s"
        params.append(year)

    # Validate sort order
    if sort not in ['asc', 'desc']:
        sort = 'desc'

    query += f" ORDER BY activity_date {sort.upper()}"

    cursor.execute(query, params)
    achievements = cursor.fetchall()

    # Get list of distinct years for dropdown
    cursor.execute("""
        SELECT DISTINCT YEAR(activity_date) as year 
        FROM achievements 
        WHERE status = 'approved' 
        ORDER BY year DESC
    """)
    years = [row['year'] for row in cursor.fetchall()]

    db.close()

    return render_template(
        'index.html',
        achievements=achievements,
        years=years,
        selected_year=year,
        sort_order=sort
    )
@app.route('/')
def home():
    return redirect(url_for('index'))

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        student_name = request.form['student_name']
        activity_details = request.form['activity_details']
        organized_by = request.form['organized_by']
        activity_date = request.form['activity_date']
        remark = request.form['remark']
        file = request.files['certificate']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            db = connect_db()
            cursor = db.cursor()
            cursor.execute(""" 
                INSERT INTO achievements 
                (student_name, activity_details, organized_by, activity_date, remark, certificate, status) 
                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            """, (student_name, activity_details, organized_by, activity_date, remark, filename))
            db.commit()
            db.close()

            flash('Achievement submitted successfully and is awaiting approval')
            return redirect(url_for('submit'))
        else:
            flash('Invalid file format. Please upload allowed files only.')

    return render_template('submit.html')
@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))

    student_id = session['user_id']
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('project_title')
        description = request.form.get('description')
        technologies = request.form.get('technologies')
        image_file = request.files.get('project_image')

        image_filename = None
        if image_file and image_file.filename != '':
            if '.' in image_file.filename and image_file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                image_filename = secure_filename(image_file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                image_file.save(image_path)

        if title and description and technologies:
            cursor.execute("""
                INSERT INTO student_submissions (student_id, project_title, description, technologies, status, image)
                VALUES (%s, %s, %s, %s, 'pending', %s)
            """, (student_id, title, description, technologies, image_filename))
            conn.commit()
            flash('Project submitted successfully with image!')

    # Fetch submissions
    cursor.execute("""
        SELECT project_title, description, technologies, status, image
        FROM student_submissions
        WHERE student_id = %s
        ORDER BY created_at DESC
    """, (student_id,))
    submissions = cursor.fetchall()

    status_counts = {'approved': 0, 'pending': 0, 'rejected': 0}
    for sub in submissions:
        status_counts[sub[3]] += 1

    submission_dicts = [
        {
            'project_title': sub[0],
            'description': sub[1],
            'technologies': sub[2],
            'status': sub[3],
            'image': sub[4]
        } for sub in submissions
    ]

    cursor.close()
    conn.close()

    return render_template('student_dashboard.html',
                           submissions=submission_dicts,
                           approved_count=status_counts['approved'],
                           pending_count=status_counts['pending'],
                           rejected_count=status_counts['rejected'])
@app.route('/staffdashboard', methods=['GET', 'POST'])
def staff_dashboard():
    if not session.get('user_id') or session.get('role') != 'staff':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # === Handle Learning Resource Upload ===
        if request.form.get('resource_title'):
            title = request.form.get('resource_title')
            category = request.form.get('resource_category')
            url = request.form.get('resource_url')  # optional external link
            file = request.files.get('resource_file')  # optional uploaded file

            resource_url = None
            if url and url.strip().startswith('http'):
                resource_url = url.strip()
            elif file and file.filename != '':
                filename = secure_filename(file.filename)
                save_path = os.path.join('static/uploads', filename)
                file.save(save_path)
                resource_url = filename

            if title and category and resource_url:
                cursor.execute("""
                    INSERT INTO learning_resources (title, url, category, uploaded_by)
                    VALUES (%s, %s, %s, %s)
                """, (title, resource_url, category, session['user_id']))
                conn.commit()
                flash('Learning resource shared successfully!', 'success')
            else:
                flash('All fields are required for sharing learning resources.', 'danger')

        # === Handle Announcement Upload ===
        elif request.form.get('title') and request.form.get('description'):
            title = request.form.get('title')
            description = request.form.get('description')
            file = request.files.get('notice_file')

            if file and file.filename != '':
                filename = secure_filename(file.filename)
                save_path = os.path.join('static/announcements', filename)
                file.save(save_path)

                cursor.execute("""
                    INSERT INTO announcements (title, description, filename, uploaded_by)
                    VALUES (%s, %s, %s, %s)
                """, (title, description, filename, session['user_id']))
                conn.commit()
                flash('Announcement uploaded successfully!', 'success')
            else:
                flash('Please upload a valid file.', 'danger')

        # === Handle Attendance Upload ===
        elif request.form.get('class_name') and request.files.get('attendance_file'):
            class_name = request.form.get('class_name')
            division = request.form.get('division')
            academic_year = request.form.get('academic_year')
            file = request.files.get('attendance_file')

            if class_name and division and academic_year and file and file.filename != '':
                filename = secure_filename(file.filename)
                save_path = os.path.join('static/study_materials', filename)
                file.save(save_path)

                cursor.execute("""
                    INSERT INTO attendance (class_name, division, academic_year, filename, uploaded_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, (class_name, division, academic_year, filename, session['user_id']))
                conn.commit()
                flash('Attendance uploaded successfully!', 'success')
            else:
                flash('All fields are required for attendance upload.', 'danger')

    # === Fetch student submissions
    cursor.execute("""
        SELECT ss.*, u.full_name AS student_name
        FROM student_submissions ss
        JOIN users u ON ss.student_id = u.id
        ORDER BY ss.created_at DESC
    """)
    submissions = cursor.fetchall()

    # === Fetch announcements
    cursor.execute("""
        SELECT a.id, a.title, a.description, a.filename, a.uploaded_at, u.full_name AS uploader
        FROM announcements a
        JOIN users u ON a.uploaded_by = u.id
        ORDER BY a.uploaded_at DESC
    """)
    announcements = cursor.fetchall()

    # === Fetch attendance uploaded by this staff
    cursor.execute("""
        SELECT a.*, u.full_name AS uploader
        FROM attendance a
        JOIN users u ON a.uploaded_by = u.id
        WHERE a.uploaded_by = %s
        ORDER BY a.uploaded_at DESC
    """, (session['user_id'],))
    attendance = cursor.fetchall()

    # === Fetch learning resources
    cursor.execute("""
        SELECT lr.*, u.full_name AS uploader
        FROM learning_resources lr
        LEFT JOIN users u ON lr.uploaded_by = u.id
        ORDER BY lr.id DESC
    """)
    learning_resources = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'staff_dashboard.html',
        submissions=submissions,
        announcements=announcements,
        attendance=attendance,
        learning_resources=learning_resources
    )
@app.route('/delete_learning_resource/<int:id>')
def delete_learning_resource(id):
    # Ensure only staff or admin can delete
    if session.get('role') not in ['admin', 'staff']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM learning_resources WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Learning resource deleted successfully.', 'success')
    return redirect(url_for('study_materials'))
@app.route('/delete_announcement/<int:announcement_id>')
def delete_announcement(announcement_id):
    if 'user_id' not in session or session.get('role') not in ['admin', 'staff']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    # Get filename to delete file from disk
    cursor.execute("SELECT filename FROM announcements WHERE id = %s", (announcement_id,))
    result = cursor.fetchone()

    if result:
        filepath = os.path.join('static', 'announcements', result['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)

        cursor.execute("DELETE FROM announcements WHERE id = %s", (announcement_id,))
        conn.commit()
        flash("Announcement deleted.", "success")
    else:
        flash("Announcement not found.", "warning")

    cursor.close()
    conn.close()
    return redirect(request.referrer or url_for('staff_dashboard'))
@app.route('/admin/student-submissions')
def view_student_submissions():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, u.full_name 
        FROM student_submissions s 
        JOIN users u ON s.student_id = u.id 
        WHERE s.status = 'pending'
    """)
    submissions = cursor.fetchall()
    conn.close()

    return render_template('admin.html', student_submissions=submissions)

@app.route('/admin/approve-submission/<int:id>')
def approve_submission(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE student_submissions SET status='approved' WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash('Submission approved.')
    return redirect(url_for('view_student_submissions'))

@app.route('/admin/reject-submission/<int:id>')
def reject_submission(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE student_submissions SET status='rejected' WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash('Submission rejected.')
    return redirect(url_for('view_student_submissions'))
# ----------------- ADMIN ROUTES -----------------

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            flash('Login successful')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password')
    return render_template('admin_login.html')


# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully')
    return redirect(url_for('admin_login'))


# Admin dashboard (combined view)
@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash('You must be logged in as an admin to access this page')
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor(dictionary=True)

    # Pending achievements
    cursor.execute("SELECT * FROM achievements WHERE status = 'pending'")
    achievements = cursor.fetchall()

    # Pending users
    cursor.execute("SELECT * FROM users WHERE is_approved = FALSE")
    pending_users = cursor.fetchall()

    # Pending student submissions (projects/technologies)
    cursor.execute("""
        SELECT s.*, u.full_name
        FROM student_submissions s
        JOIN users u ON s.student_id = u.id
        WHERE s.status = 'pending'
    """)
    student_submissions = cursor.fetchall()

    db.close()
    return render_template(
        'admin.html',
        achievements=achievements,
        pending_users=pending_users,
        student_submissions=student_submissions
    )

# Approve Achievement
@app.route('/admin/approve/<int:id>')
def approve(id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to approve achievements')
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("UPDATE achievements SET status='approved' WHERE id=%s", (id,))
    db.commit()
    db.close()

    flash('Achievement approved successfully')
    return redirect(url_for('admin'))


# Reject Achievement
@app.route('/admin/reject/<int:id>')
def reject(id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to reject achievements')
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("UPDATE achievements SET status='rejected' WHERE id=%s", (id,))
    db.commit()
    db.close()

    flash('Achievement rejected successfully')
    return redirect(url_for('admin'))


# Delete Achievement
@app.route('/admin/delete/<int:id>')
def delete_achievement(id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to delete achievements')
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM achievements WHERE id = %s", (id,))
    db.commit()
    db.close()

    flash('Achievement deleted successfully')
    return redirect(url_for('admin'))


# Approve User
@app.route('/approve_user/<int:user_id>')
def approve_user(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET is_approved = TRUE WHERE id = %s", (user_id,))
    db.commit()
    db.close()

    flash('User approved successfully.', 'success')
    return redirect(url_for('admin'))


# Reject User
@app.route('/reject_user/<int:user_id>')
def reject_user(user_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    db.close()

    flash('User rejected and removed.', 'danger')
    return redirect(url_for('admin'))


# Prevent admin registration
@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    flash('Registration is only available for the admin')
    return redirect(url_for('admin_login'))
@app.route('/events')
def events():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM events ORDER BY date DESC")
    events = cursor.fetchall()
    db.close()
    return render_template('events.html', events=events, event_to_edit=None)
@app.route('/add_event', methods=['POST'])
def add_event():
    if not session.get('admin'):
        flash("You must be logged in as an admin.")
        return redirect(url_for('admin_login'))

    title = request.form['title']
    description = request.form['description']
    date = request.form['date']
    image = request.files.get('image')

    image_filename = None
    if image and image.filename and allowed_file(image.filename):
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO events (title, description, date, image) VALUES (%s, %s, %s, %s)",
                (title, description, date, image_filename))
    db.commit()
    db.close()

    flash("Event added successfully.")
    return redirect(url_for('events'))
@app.route('/edit_event/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    if not session.get('admin'):
        flash("You must be logged in as an admin.")
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        image = request.files.get('image')

        if image and image.filename and allowed_file(image.filename):
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            cursor.execute("UPDATE events SET title=%s, description=%s, date=%s, image=%s WHERE id=%s",
                        (title, description, date, image_filename, id))
        else:
            cursor.execute("UPDATE events SET title=%s, description=%s, date=%s WHERE id=%s",
                        (title, description, date, id))

        db.commit()
        db.close()
        flash("Event updated successfully.")
        return redirect(url_for('events'))

    cursor.execute("SELECT * FROM events WHERE id=%s", (id,))
    event_to_edit = cursor.fetchone()

    cursor.execute("SELECT * FROM events ORDER BY date DESC")
    events = cursor.fetchall()
    db.close()
    return render_template('events.html', events=events, event_to_edit=event_to_edit)
@app.route('/delete_event/<int:id>', methods=['POST'])
def delete_event(id):
    if not session.get('admin'):
        flash("You must be logged in as an admin.")
        return redirect(url_for('admin_login'))

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM events WHERE id = %s", (id,))
    db.commit()
    db.close()
    flash("Event deleted successfully.")
    return redirect(url_for('events'))
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            password_raw = request.form.get('password', '')
            role = request.form.get('role', '').strip()
            student_class = request.form.get('student_class') if role.lower() == 'student' else None

            # Basic validation
            if not all([full_name, email, password_raw, role]):
                flash('All fields are required.', 'warning')
                return redirect(url_for('register'))

            if role.lower() == 'student' and not student_class:
                flash('Please select your class.', 'warning')
                return redirect(url_for('register'))

            password = generate_password_hash(password_raw)

            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (full_name, email, password, role, is_approved, student_class) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (full_name, email, password, role.lower(), False, student_class))
            conn.commit()
            conn.close()

            flash('Registration successful! Awaiting admin approval.', 'info')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password_input):
            if not user['is_approved']:
                flash('Your account is awaiting admin approval.', 'warning')
                return redirect(url_for('login'))

            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['full_name']

            # Store class info for students
            if user['role'] == 'student':
                session['student_class'] = user.get('class')  # `class` must be a column in the users table

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role')

    if role == 'student':
        return redirect(url_for('student_dashboard'))
    elif role == 'staff':
        return redirect(url_for('staff_dashboard'))
    else:
        return "Unauthorized access or unknown role.", 403

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))
@app.route('/dev_club')
def dev_club():
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)  # Use dictionary cursor for easier access

        # Fetch approved projects with student names and optional image
        query = """
            SELECT ss.project_title, ss.description, ss.technologies, ss.image, u.full_name AS student_name
            FROM student_submissions ss
            JOIN users u ON ss.student_id = u.id
            WHERE ss.status = 'approved'
            ORDER BY ss.created_at DESC
        """
        cursor.execute(query)
        approved_projects = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('dev_club.html', approved_projects=approved_projects)

    except mysql.connector.Error as err:
        print("Database error:", err)
        flash("Database connection failed.")
        return redirect(url_for('department_home'))
@app.route('/study_materials')
def study_materials():
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        # Get filters from query parameters
        subject_filter = request.args.get('subject')
        class_filter = request.args.get('class')
        semester_filter = request.args.get('semester')

        # Fetch distinct values for filters
        cursor.execute("SELECT DISTINCT subject FROM study_materials")
        all_subjects = [row['subject'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT class FROM study_materials")
        all_classes = [row['class'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT semester FROM study_materials")
        all_semesters = [row['semester'] for row in cursor.fetchall()]

        # Fetch study materials with filters
        query = """
            SELECT sm.*, u.full_name AS staff_name
            FROM study_materials sm
            JOIN users u ON sm.staff_id = u.id
            WHERE 1=1
        """
        params = []

        if subject_filter:
            query += " AND sm.subject = %s"
            params.append(subject_filter)

        if class_filter:
            query += " AND sm.class = %s"
            params.append(class_filter)

        if semester_filter:
            query += " AND sm.semester = %s"
            params.append(semester_filter)

        query += " ORDER BY sm.uploaded_at DESC"
        cursor.execute(query, params)
        materials = cursor.fetchall()

        # === Announcements ===
        cursor.execute("""
            SELECT a.id, a.title, a.description, a.filename, a.uploaded_at, u.full_name AS uploader
            FROM announcements a
            JOIN users u ON a.uploaded_by = u.id
            ORDER BY a.uploaded_at DESC
        """)
        announcements = cursor.fetchall()

        # === Attendance Filtering by Role ===
        role = session.get('role')
        user_id = session.get('user_id')
        attendance = []
        if role == 'student':
            cursor.execute("SELECT student_class FROM users WHERE id = %s", (user_id,))
            student = cursor.fetchone()
            if student:
                cursor.execute("""
            SELECT * FROM attendance
            WHERE class_name = %s
            ORDER BY uploaded_at DESC
        """, (student['student_class'],))
                attendance = cursor.fetchall()
        else:
            cursor.execute("SELECT * FROM attendance ORDER BY uploaded_at DESC")
            attendance = cursor.fetchall()


        # === Learning Resources ===
        cursor.execute("""
            SELECT lr.id, lr.title, lr.url, lr.category, u.full_name AS uploader
            FROM learning_resources lr
            JOIN users u ON lr.uploaded_by = u.id
            ORDER BY lr.id DESC
        """)
        learning_resources = cursor.fetchall()

        return render_template(
            'study_materials.html',
            materials=materials,
            all_subjects=all_subjects,
            all_classes=all_classes,
            all_semesters=all_semesters,
            selected_subject=subject_filter,
            selected_class=class_filter,
            selected_semester=semester_filter,
            announcements=announcements,
            attendance=attendance,
            learning_resources=learning_resources
        )

    except Exception as e:
        print("❌ Error in /study_materials route:", e)
        return "Something went wrong while loading study materials.", 500

    finally:
        if cursor: cursor.close()
        if conn: conn.close()
@app.route('/upload_material', methods=['POST'])
def upload_material():
    if 'user_id' not in session or session.get('role') != 'staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    # Common form fields
    title = request.form.get('title')
    subject = request.form.get('subject')
    class_name = request.form.get('class')  # This refers to 'class' column in study_materials table
    semester = request.form.get('semester')
    resource_type = request.form.get('resource_type')  # 'file' or 'link'

    conn = connect_db()
    cursor = conn.cursor()

    try:
        if resource_type == 'link':
            # Learning resource upload (YouTube, GitHub, etc.)
            category = request.form.get('category')
            link = request.form.get('link')

            if not all([title, category, link]):
                flash("All fields are required for a learning resource.", "danger")
                return redirect(url_for('study_materials'))

            cursor.execute("""
                INSERT INTO learning_resources (title, category, url, uploaded_by)
                VALUES (%s, %s, %s, %s)
            """, (title, category, link, session['user_id']))
            conn.commit()
            flash("Learning resource uploaded successfully.", "success")

        else:
            # Study material upload (PDFs, docs, etc.)
            file = request.files.get('file')
            if not all([title, subject, class_name, semester, file]) or file.filename == '':
                flash("All fields are required for study material.", "danger")
                return redirect(url_for('study_materials'))

            filename = secure_filename(file.filename)
            save_path = os.path.join('static/study_materials', filename)

            # Avoid overwriting existing files
            if os.path.exists(save_path):
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{int(time.time())}{ext}"
                save_path = os.path.join('static/study_materials', filename)

            file.save(save_path)

            cursor.execute("""
                INSERT INTO study_materials (title, subject, class, semester, filename, staff_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, subject, class_name, semester, filename, session['user_id']))
            conn.commit()
            flash("Study material uploaded successfully.", "success")

    except Exception as e:
        print("❌ Error uploading material:", e)
        flash("An error occurred during upload.", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('study_materials'))
@app.route('/upload_attendance', methods=['GET', 'POST'])
def upload_attendance():
    # Redirect GET requests to dashboard
    if request.method == 'GET':
        return redirect(url_for('staff_dashboard'))

    # Ensure only logged-in staff can upload
    if 'user_id' not in session or session.get('role') != 'staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    # Collect form data
    file = request.files.get('attendance_file')
    class_name = request.form.get('class_name')         # e.g., FE, SE, TE
    division = request.form.get('division')             # e.g., A, B
    academic_year = request.form.get('academic_year')   # e.g., 2024-25

    # Check all fields are provided
    if not all([file, class_name, division, academic_year]):
        flash("All fields are required.", "danger")
        return redirect(url_for('staff_dashboard'))

    # Validate file extension
    allowed_extensions = ('.xlsx', '.xls')
    if not file.filename.lower().endswith(allowed_extensions):
        flash("Please upload a valid Excel (.xlsx or .xls) file.", "danger")
        return redirect(url_for('staff_dashboard'))

    try:
        # Secure the filename
        filename = secure_filename(file.filename)

        # Create directory if it doesn't exist
        save_dir = os.path.join('static', 'attendance_files')
        os.makedirs(save_dir, exist_ok=True)

        # Ensure unique filename to prevent overwrite
        save_path = os.path.join(save_dir, filename)
        if os.path.exists(save_path):
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{int(time.time())}{ext}"
            save_path = os.path.join(save_dir, filename)

        # Save the file
        file.save(save_path)

        # Save record to DB
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance (filename, class_name, division, academic_year, uploaded_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (filename, class_name, division, academic_year, session['user_id']))
        conn.commit()

        flash("✅ Attendance uploaded successfully!", "success")

    except Exception as e:
        print("❌ Error uploading attendance:", e)
        flash("An error occurred while uploading attendance.", "danger")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    return redirect(url_for('staff_dashboard'))
@app.route('/delete_material/<int:material_id>')
def delete_material(material_id):
    if 'user_id' not in session or session.get('role') != 'staff':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('login'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM study_materials WHERE id = %s", (material_id,))
    file_data = cursor.fetchone()
    
    if file_data:
        filepath = os.path.join('static/study_materials', file_data[0])
        if os.path.exists(filepath):
            os.remove(filepath)
        cursor.execute("DELETE FROM study_materials WHERE id = %s", (material_id,))
        conn.commit()
        flash("Material deleted successfully.", "success")

    cursor.close()
    conn.close()
    return redirect(url_for('study_materials'))
@app.route('/download_material/<filename>')
def download_material(filename):
    return send_from_directory('static/study_materials', filename, as_attachment=True)
# ----------------- EXPORT -----------------

@app.route('/export', methods=['GET'])
def export_achievements():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM achievements WHERE status = 'approved'")
    achievements = cursor.fetchall()
    db.close()

    data = []
    for index, achievement in enumerate(achievements, start=1):
        data.append([ 
            index,
            achievement['student_name'],
            achievement['activity_details'],
            achievement['organized_by'],
            achievement['activity_date'],
            achievement['remark']
        ])

    df = pd.DataFrame(data, columns=['Sr No', 'Student Name', 'Activity Details', 'Organized By', 'Date', 'Remark'])
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="approved_achievements.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ----------------- START APP -----------------

if __name__ == '__main__':
    app.run(debug=True)