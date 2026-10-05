USE attendease;

INSERT INTO teachers (name,email,department) VALUES
('Prof. Patil','patil@college.com','Computer Science'),
('Prof. Sharma','sharma@college.com','Computer Science'),
('Prof. Joshi','joshi@college.com','Mathematics'),
('Prof. More','more@college.com','Computer Science');

INSERT INTO subjects (name,code,teacher_id,planned_lectures) VALUES
('Python','PY101',1,40),
('DBMS','DBMS101',2,40),
('Mathematics','MATH101',3,40),
('Web Technology','WT101',4,40);

INSERT INTO timetable (day_name,lecture_time,subject_id,teacher_id,room) VALUES
('Monday','09:00 AM - 10:00 AM',1,1,'Lab 1'),
('Monday','10:00 AM - 11:00 AM',2,2,'Room 204'),
('Monday','11:00 AM - 12:00 PM',3,3,'Room 301'),
('Tuesday','09:00 AM - 10:00 AM',4,4,'Lab 2'),
('Tuesday','10:00 AM - 11:00 AM',1,1,'Lab 1'),
('Wednesday','10:00 AM - 11:00 AM',2,2,'Room 204'),
('Thursday','09:00 AM - 10:00 AM',3,3,'Room 301'),
('Friday','11:00 AM - 12:00 PM',4,4,'Lab 2');

INSERT INTO reminders (title,message,reminder_date,reminder_time) VALUES
('Python Lecture','Your Python lecture is scheduled.','2026-10-05','09:00 AM'),
('DBMS Lecture','Your DBMS lecture is scheduled.','2026-10-05','10:00 AM'),
('Attendance Alert','Maintain at least 75% attendance.','2026-10-05','All Day');
