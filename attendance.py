from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from models import db, Attendance
from face_recognition_module.main import recognize_face_from_camera  # Function for live face recognition
import datetime

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    if request.method == 'POST':
        # Use live face recognition to mark attendance
        student_id = recognize_face_from_camera()  # Call the live recognition function
        if student_id:
            # Check if attendance is already marked for today
            existing_attendance = Attendance.query.filter_by(
                student_id=student_id,
                date=datetime.date.today()
            ).first()
            if existing_attendance:
                flash('Attendance already marked for today!', 'warning')
            else:
                # Mark attendance
                attendance = Attendance(student_id=student_id, date=datetime.datetime.now())
                db.session.add(attendance)
                db.session.commit()
                flash('Attendance marked successfully!', 'success')
        else:
            flash('Face not recognized!', 'error')
        return redirect(url_for('attendance.mark_attendance'))
    return render_template('mark_attendance.html')