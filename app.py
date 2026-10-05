import os
from functools import wraps
from datetime import datetime
from urllib.parse import urlparse

import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

def db():
    url = os.getenv("MYSQL_URL")
    if url:
        p = urlparse(url)
        return pymysql.connect(
            host=p.hostname,
            port=p.port or 3306,
            user=p.username,
            password=p.password,
            database=p.path.lstrip("/"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "attendease"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def student_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "student_id" not in session:
            flash("Please login first.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            flash("Admin login required.", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        f = request.form
        required = ["name","email","password","course","year","semester"]
        if any(not f.get(x) for x in required):
            flash("Please fill all required fields.", "danger")
            return render_template("register.html")

        try:
            conn = db()
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO students
                (name,email,password_hash,mobile,roll_no,enrollment,course,year,
                 semester,division,academic_year,dob,gender,address)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (
                    f["name"], f["email"].strip().lower(),
                    generate_password_hash(f["password"]),
                    f.get("mobile"), f.get("roll_no"), f.get("enrollment"),
                    f.get("course"), f.get("year"), f.get("semester"),
                    f.get("division"), f.get("academic_year"),
                    f.get("dob") or None, f.get("gender"), f.get("address")
                ))
            conn.close()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        except pymysql.err.IntegrityError:
            flash("This email is already registered.", "danger")
        except Exception as e:
            flash("Database error: " + str(e), "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students WHERE email=%s", (email,))
            student = cur.fetchone()
        conn.close()
        if student and check_password_hash(student["password_hash"], password):
            session.clear()
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@student_required
def dashboard():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM students WHERE id=%s", (session["student_id"],))
        student = cur.fetchone()
        cur.execute("""SELECT COUNT(*) total,
            SUM(status='Present') present,
            SUM(status='Absent') absent
            FROM attendance WHERE student_id=%s""", (session["student_id"],))
        stats = cur.fetchone()
        cur.execute("""SELECT s.name subject, COUNT(a.id) conducted,
            COALESCE(SUM(a.status='Present'),0) present
            FROM subjects s LEFT JOIN attendance a
            ON a.subject_id=s.id AND a.student_id=%s
            GROUP BY s.id ORDER BY s.name""", (session["student_id"],))
        subjects = cur.fetchall()
        cur.execute("""SELECT t.*, s.name subject, te.name teacher
            FROM timetable t JOIN subjects s ON s.id=t.subject_id
            LEFT JOIN teachers te ON te.id=t.teacher_id
            ORDER BY t.id LIMIT 6""")
        upcoming = cur.fetchall()
    conn.close()
    total = stats["total"] or 0
    present = stats["present"] or 0
    absent = stats["absent"] or 0
    percentage = round(present * 100 / total, 2) if total else 0
    return render_template("dashboard.html", student=student, total=total,
        present=present, absent=absent, percentage=percentage,
        subjects=subjects, upcoming=upcoming)

@app.route("/attendance")
@student_required
def attendance():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("""SELECT a.*, s.name subject, te.name teacher
            FROM attendance a JOIN subjects s ON s.id=a.subject_id
            LEFT JOIN teachers te ON te.id=a.teacher_id
            WHERE a.student_id=%s ORDER BY a.lecture_date DESC, a.id DESC""",
            (session["student_id"],))
        records = cur.fetchall()
    conn.close()
    return render_template("attendance.html", records=records)

@app.route("/progress")
@student_required
def progress():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("""SELECT s.name subject, s.code, s.planned_lectures,
            COUNT(a.id) conducted,
            COALESCE(SUM(a.status='Present'),0) present,
            COALESCE(SUM(a.status='Absent'),0) absent
            FROM subjects s LEFT JOIN attendance a
            ON a.subject_id=s.id AND a.student_id=%s
            GROUP BY s.id ORDER BY s.name""", (session["student_id"],))
        subjects = cur.fetchall()
    conn.close()
    for s in subjects:
        s["percentage"] = round(s["present"]*100/s["conducted"],2) if s["conducted"] else 0
        s["remaining"] = max((s["planned_lectures"] or 0)-s["conducted"],0)
    return render_template("progress.html", subjects=subjects)

@app.route("/timetable")
@student_required
def timetable():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("""SELECT t.*, s.name subject, s.code, te.name teacher
            FROM timetable t JOIN subjects s ON s.id=t.subject_id
            LEFT JOIN teachers te ON te.id=t.teacher_id
            ORDER BY FIELD(t.day_name,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), t.id""")
        rows = cur.fetchall()
    conn.close()
    return render_template("timetable.html", timetable=rows)

@app.route("/reminders")
@student_required
def reminders():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM reminders ORDER BY reminder_date, id")
        rows = cur.fetchall()
    conn.close()
    return render_template("reminders.html", reminders=rows)

@app.route("/profile")
@student_required
def profile():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM students WHERE id=%s", (session["student_id"],))
        student = cur.fetchone()
    conn.close()
    return render_template("profile.html", student=student)

@app.route("/attendance/print")
@student_required
def print_attendance():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("""SELECT a.*, s.name subject, te.name teacher
            FROM attendance a JOIN subjects s ON s.id=a.subject_id
            LEFT JOIN teachers te ON te.id=a.teacher_id
            WHERE a.student_id=%s ORDER BY a.lecture_date DESC, a.id DESC""",
            (session["student_id"],))
        records = cur.fetchall()
        cur.execute("SELECT * FROM students WHERE id=%s", (session["student_id"],))
        student = cur.fetchone()
    conn.close()
    return render_template("print_attendance.html", records=records, student=student)

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if (request.form["email"] == os.getenv("ADMIN_EMAIL","admin@attendease.com")
            and request.form["password"] == os.getenv("ADMIN_PASSWORD","admin123")):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin():
    conn = db()
    with conn.cursor() as cur:
        cur.execute("SELECT id,name,email,roll_no,course,year,semester,division FROM students ORDER BY id DESC")
        students = cur.fetchall()
        cur.execute("SELECT * FROM subjects ORDER BY name")
        subjects = cur.fetchall()
        cur.execute("SELECT * FROM teachers ORDER BY name")
        teachers = cur.fetchall()
        cur.execute("""SELECT a.id, st.name student, s.name subject, a.lecture_date,
            a.lecture_time, a.status, te.name teacher
            FROM attendance a JOIN students st ON st.id=a.student_id
            JOIN subjects s ON s.id=a.subject_id
            LEFT JOIN teachers te ON te.id=a.teacher_id
            ORDER BY a.lecture_date DESC, a.id DESC LIMIT 30""")
        attendance_rows = cur.fetchall()
    conn.close()
    return render_template("admin.html", students=students, subjects=subjects,
                           teachers=teachers, attendance_rows=attendance_rows)

@app.route("/admin/attendance/add", methods=["POST"])
@admin_required
def add_attendance():
    f = request.form
    conn = db()
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO attendance
            (student_id,subject_id,teacher_id,lecture_date,lecture_time,status)
            VALUES (%s,%s,%s,%s,%s,%s)""", (
                f["student_id"], f["subject_id"], f.get("teacher_id") or None,
                f["lecture_date"], f.get("lecture_time"), f["status"]
            ))
    conn.close()
    flash("Attendance saved successfully.", "success")
    return redirect(url_for("admin"))

@app.route("/health")
def health():
    try:
        conn = db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            result = cur.fetchone()
        conn.close()
        return {"status":"ok","database":result["ok"]}
    except Exception as e:
        return {"status":"error","message":str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
