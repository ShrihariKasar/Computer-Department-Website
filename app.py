from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
import os
import pandas as pd
from io import BytesIO
from werkzeug.utils import secure_filename
from config import DB_CONFIG, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = '3ed2e95f933aeaa2d2b21267496eac8f'

# Admin credentials - Store hashed password
ADMIN_USERNAME = 'Shrihari'
ADMIN_PASSWORD_HASH = generate_password_hash('Kasar')  # Use hashed password

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_session():
    return dict(session=session)

@app.route('/')
def index():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM achievements WHERE status = 'approved'")
    data = cursor.fetchall()
    db.close()
    return render_template('index.html', achievements=data)

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
            return redirect('/')
        else:
            flash('Invalid file format. Please upload allowed files only.')

    return render_template('submit.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            flash('Login successful')
            return redirect('/admin')
        else:
            flash('Invalid username or password')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out successfully')
    return redirect('/admin/login')

@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash('You must be logged in as an admin to access this page')
        return redirect('/admin/login')
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM achievements WHERE status = 'pending'")
    data = cursor.fetchall()
    db.close()
    return render_template('admin.html', achievements=data)

@app.route('/admin/approve/<int:id>')
def approve(id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to approve achievements')
        return redirect('/admin/login')
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("UPDATE achievements SET status='approved' WHERE id=%s", (id,))
    db.commit()
    db.close()
    flash('Achievement approved successfully')
    return redirect('/admin')

@app.route('/admin/reject/<int:id>')
def reject(id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to reject achievements')
        return redirect('/admin/login')
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("UPDATE achievements SET status='rejected' WHERE id=%s", (id,))
    db.commit()
    db.close()
    flash('Achievement rejected successfully')
    return redirect('/admin')

@app.route('/admin/delete/<int:id>')
def delete_achievement(id):
    if not session.get('admin'):
        flash('You must be logged in as an admin to delete achievements')
        return redirect('/admin/login')
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM achievements WHERE id = %s", (id,))
    db.commit()
    db.close()
    flash('Achievement deleted successfully')
    return redirect('/')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    flash('Registration is only available for the admin')
    return redirect('/admin/login')

@app.route('/export', methods=['GET'])
def export_achievements():
    db = connect_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM achievements WHERE status = 'approved'")
    achievements = cursor.fetchall()
    db.close()

    # Convert data into a pandas DataFrame
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

    # Save the DataFrame to a BytesIO object
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="approved_achievements.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == '__main__':
    app.run(debug=True)