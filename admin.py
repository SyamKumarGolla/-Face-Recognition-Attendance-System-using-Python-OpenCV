from flask import Blueprint, render_template
from models import db, Attendance, Resource, User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'Admin':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('auth.login'))
    attendance_reports = Attendance.query.all()
    resource_usage = Resource.query.all()
    users = User.query.all()
    return render_template('admin_dashboard.html', attendance_reports=attendance_reports, resource_usage=resource_usage, users=users)