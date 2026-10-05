# AttendEase - MySQL Flask Mini Project

## Features
- Multiple student registration and login
- Complete student academic/profile details
- Date-wise attendance
- Subject-wise attendance and progress
- Teacher information
- Timetable with lecture time and room
- Reminders
- Printable attendance report / Save as PDF
- Admin/Teacher panel to add attendance
- MySQL database
- Render-compatible deployment configuration

## 1. Install
Open terminal inside this folder:
```bash
python -m venv venv
```
Windows:
```bash
venv\Scripts\activate
```
Then:
```bash
pip install -r requirements.txt
```

## 2. MySQL Workbench
Open MySQL Workbench and run `schema.sql`.

Then run `seed.sql`.

This creates:
- attendease database
- students
- teachers
- subjects
- attendance
- timetable
- reminders

## 3. Environment
Copy `.env.example` to `.env`.

Example:
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=attendease
ADMIN_EMAIL=admin@attendease.com
ADMIN_PASSWORD=admin123
SECRET_KEY=change-this-to-a-random-secret

Do NOT upload `.env` to GitHub.

## 4. Run
```bash
python app.py
```
Open:
http://127.0.0.1:5000

## 5. Student demo
1. Register a student.
2. Login.
3. Open Dashboard.
4. Open Attendance.
5. Open Progress.
6. Open Timetable.
7. Open Reminders.
8. Open Profile.
9. Use Print Report.

## 6. Add attendance
Open:
http://127.0.0.1:5000/admin/login

Default local admin:
Email: admin@attendease.com
Password: admin123

Add Present/Absent records for registered students.

## 7. Deployment
The included `render.yaml` expects an external MySQL-compatible database.
Create a MySQL database with your chosen provider, then put its host/user/password/database/port into Render environment variables.

If the provider gives a full MySQL connection URL, you can instead set:
MYSQL_URL=mysql://user:password@host:3306/database

The web service starts with:
gunicorn app:app

After deployment, test:
YOUR_DOMAIN/health

It should return:
{"status":"ok","database":1}
