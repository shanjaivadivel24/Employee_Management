from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# DB init
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT,
        password TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        emp_id TEXT PRIMARY KEY,
        name TEXT,
        image_path TEXT,
        phone TEXT,
        department TEXT,
        salary INTEGER,
        gender TEXT,
        status TEXT
    )
    ''')

    conn.commit()
    conn.close()

# Uncomment once to run DB init
# init_db()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        conn = get_db_connection()
        conn.execute("INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
                     (name, email, phone, password))
        conn.commit()
        conn.close()
        flash("Registered successfully. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('main'))
        else:
            flash("Invalid login credentials")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('search')
    conn = get_db_connection()
    if search_query:
        employees = conn.execute("SELECT * FROM employees WHERE emp_id LIKE ? OR name LIKE ?", 
                                 (f"%{search_query}%", f"%{search_query}%")).fetchall()
    else:
        employees = conn.execute("SELECT * FROM employees").fetchall()
    conn.close()
    return render_template('dashboard.html', employees=employees)

@app.route('/delete/<emp_id>')
def delete(emp_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("DELETE FROM employees WHERE emp_id = ?", (emp_id,))
    conn.commit()
    conn.close()
    flash("Employee deleted.")
    return redirect(url_for('dashboard'))

@app.route('/edit/<emp_id>', methods=['GET', 'POST'])
def edit(emp_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    emp = conn.execute("SELECT * FROM employees WHERE emp_id = ?", (emp_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        department = request.form['department']
        salary = request.form['salary']
        gender = request.form['gender']
        status = request.form['status']

        image = request.files['image']
        if image and image.filename != '':
            image_path = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
        else:
            image_path = emp['image_path']

        conn.execute("""
            UPDATE employees SET name=?, phone=?, department=?, salary=?, image_path=?, gender=?, status=?
            WHERE emp_id=?
        """, (name, phone, department, salary, image_path, gender, status, emp_id))
        conn.commit()
        conn.close()
        flash("Employee updated successfully.")
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit.html', emp=emp)

@app.route('/salary-update', methods=['GET', 'POST'])
def salary_update():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        new_salary = request.form['salary']

        conn.execute("UPDATE employees SET salary = ? WHERE emp_id = ?", (new_salary, emp_id))
        conn.commit()
        conn.close()
        flash("Salary updated successfully.")
        return redirect(url_for('dashboard'))

    employees = conn.execute("SELECT emp_id, name FROM employees").fetchall()
    conn.close()
    return render_template('salary_update.html', employees=employees)

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        name = request.form['name']
        phone = request.form['phone']
        department = request.form['department']
        salary = request.form['salary']
        gender = request.form['gender']
        status = request.form['status']
        image = request.files['image']

        # Save image
        image_path = ""
        if image and image.filename != '':
            image_path = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO employees (emp_id, name, phone, department, salary, image_path, gender, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (emp_id, name, phone, department, salary, image_path, gender, status))
        conn.commit()
        conn.close()
        flash("Employee added successfully.")
        return redirect(url_for('dashboard'))

    return render_template('add_employee.html')

if __name__ == "__main__":
    init_db()
    app.run(debug=True)