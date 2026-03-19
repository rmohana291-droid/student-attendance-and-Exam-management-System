from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import db, Student, Subject, Attendance, Mark
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'

db.init_app(app)

# Create tables and add sample data
with app.app_context():
    db.create_all()

    # Add sample admin if not exists
    if not Student.query.filter_by(roll_no='ADMIN001').first():
        admin = Student(roll_no='ADMIN001', name='Admin', register_no='ADMIN001')
        db.session.add(admin)

    # Add sample students for testing
    if Student.query.count() == 1:  # Only admin exists
        students_data = [
            {'roll_no': '2024001', 'name': 'John Doe', 'register_no': 'REG002'},
            {'roll_no': '2024002', 'name': 'Jane Smith', 'register_no': 'REG002'},
            {'roll_no': '2024003', 'name': 'Bob Johnson', 'register_no': 'REG003'},
            {'roll_no': '2024004', 'name': 'Alice Williams', 'register_no': 'REG004'},
            {'roll_no': '2024005', 'name': 'Charlie Brown', 'register_no': 'REG005'},
        ]

        for student_data in students_data:
            student = Student(**student_data)
            db.session.add(student)

        db.session.commit()

    # Add sample subjects
    if Subject.query.count() == 0:
        subjects_data = [
            {'name': 'Mathematics', 'code': 'MATH101'},
            {'name': 'Physics', 'code': 'PHY101'},
            {'name': 'Chemistry', 'code': 'CHEM101'},
            {'name': 'Computer Science', 'code': 'CS101'},
            {'name': 'English', 'code': 'ENG101'},
        ]

        for subject_data in subjects_data:
            subject = Subject(**subject_data)
            db.session.add(subject)

        db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'admin123':  # Simple password check
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid password!')
    return render_template('admin.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    students = Student.query.all()
    subjects = Subject.query.all()

    # Calculate attendance percentages
    attendance_data = []
    for student in students:
        if student.roll_no != 'ADMIN001':  # Exclude admin from attendance list
            total_classes = Attendance.query.filter_by(student_id=student.id).count()
            if total_classes > 0:
                present = Attendance.query.filter_by(student_id=student.id, status='Present').count()
                percentage = (present / total_classes) * 100
            else:
                percentage = 0
            attendance_data.append({
                'roll_no': student.roll_no,
                'name': student.name,
                'percentage': round(percentage, 2)
            })

    return render_template('admin_dashboard.html', students=students, subjects=subjects,
                           attendance_data=attendance_data)


@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']

        # Check if subject already exists
        existing_subject = Subject.query.filter_by(code=code).first()
        if existing_subject:
            flash('Subject with this code already exists!')
            return redirect(url_for('add_subject'))

        subject = Subject(name=name, code=code)
        db.session.add(subject)
        db.session.commit()

        flash('Subject added successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_subject.html')


@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    subjects = Subject.query.all()
    students = Student.query.filter(Student.roll_no != 'ADMIN001').all()  # Exclude admin

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

        # Check if attendance already marked for this subject and date
        existing_attendance = Attendance.query.filter_by(
            subject_id=subject_id,
            date=date
        ).first()

        if existing_attendance:
            flash('Attendance already marked for this subject on this date!')
            return redirect(url_for('mark_attendance'))

        attendance_count = 0
        for student in students:
            status = request.form.get(f'attendance_{student.id}')
            if status and status != '':  # Only add if status is selected
                attendance = Attendance(
                    student_id=student.id,
                    subject_id=subject_id,
                    date=date,
                    status=status
                )
                db.session.add(attendance)
                attendance_count += 1

        if attendance_count > 0:
            db.session.commit()
            flash(f'Attendance marked successfully for {attendance_count} students!')
        else:
            flash('No attendance data to save!')

        return redirect(url_for('admin_dashboard'))

    # Pass current date to template
    current_date = datetime.now().date()
    return render_template('mark_attendance.html',
                           subjects=subjects,
                           students=students,
                           now=current_date)


@app.route('/upload_marks', methods=['GET', 'POST'])
def upload_marks():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    subjects = Subject.query.all()
    students = Student.query.filter(Student.roll_no != 'ADMIN001').all()  # Exclude admin

    if request.method == 'POST':
        subject_id = request.form['subject_id']
        exam_type = request.form['exam_type']
        total_marks = float(request.form['total_marks'])

        marks_count = 0
        for student in students:
            marks_obtained = request.form.get(f'marks_{student.id}')
            if marks_obtained and marks_obtained.strip():  # Only add if marks are entered
                # Check if marks already exist for this student, subject, and exam type
                existing_marks = Mark.query.filter_by(
                    student_id=student.id,
                    subject_id=subject_id,
                    exam_type=exam_type
                ).first()

                if existing_marks:
                    # Update existing marks
                    existing_marks.marks_obtained = float(marks_obtained)
                    existing_marks.total_marks = total_marks
                else:
                    # Create new marks entry
                    mark = Mark(
                        student_id=student.id,
                        subject_id=subject_id,
                        marks_obtained=float(marks_obtained),
                        total_marks=total_marks,
                        exam_type=exam_type
                    )
                    db.session.add(mark)
                marks_count += 1

        if marks_count > 0:
            db.session.commit()
            flash(f'Marks uploaded/updated successfully for {marks_count} students!')
        else:
            flash('No marks data to save!')

        return redirect(url_for('admin_dashboard'))

    return render_template('upload_marks.html', subjects=subjects, students=students)


@app.route('/student', methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        register_no = request.form['register_no']
        student = Student.query.filter_by(register_no=register_no).first()

        if student and student.roll_no != 'ADMIN001':  # Exclude admin login
            # Calculate attendance percentage
            total_classes = Attendance.query.filter_by(student_id=student.id).count()
            if total_classes > 0:
                present = Attendance.query.filter_by(student_id=student.id, status='Present').count()
                attendance_percentage = (present / total_classes) * 100
            else:
                attendance_percentage = 0

            # Get marks with subject details
            marks = Mark.query.filter_by(student_id=student.id).all()

            # Get attendance details by subject
            attendance_by_subject = []
            subjects = Subject.query.all()
            for subject in subjects:
                subject_classes = Attendance.query.filter_by(
                    student_id=student.id,
                    subject_id=subject.id
                ).count()
                if subject_classes > 0:
                    subject_present = Attendance.query.filter_by(
                        student_id=student.id,
                        subject_id=subject.id,
                        status='Present'
                    ).count()
                    subject_percentage = (subject_present / subject_classes) * 100
                else:
                    subject_percentage = 0

                attendance_by_subject.append({
                    'subject_name': subject.name,
                    'subject_code': subject.code,
                    'percentage': round(subject_percentage, 2)
                })

            return render_template('student.html',
                                   student=student,
                                   attendance_percentage=round(attendance_percentage, 2),
                                   marks=marks,
                                   attendance_by_subject=attendance_by_subject)
        else:
            flash('Student not found! Please check your register number.')

    return render_template('student.html')


@app.route('/view_students')
def view_students():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    students = Student.query.filter(Student.roll_no != 'ADMIN001').all()
    return render_template('view_students.html', students=students)


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    if request.method == 'POST':
        roll_no = request.form['roll_no']
        name = request.form['name']
        register_no = request.form['register_no']

        # Check if student already exists
        existing_student = Student.query.filter(
            (Student.roll_no == roll_no) | (Student.register_no == register_no)
        ).first()

        if existing_student:
            flash('Student with this Roll No or Register No already exists!')
            return redirect(url_for('add_student'))

        student = Student(roll_no=roll_no, name=name, register_no=register_no)
        db.session.add(student)
        db.session.commit()

        flash('Student added successfully!')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_student.html')


@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out successfully!')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)