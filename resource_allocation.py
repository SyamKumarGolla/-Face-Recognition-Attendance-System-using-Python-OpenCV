from flask import Blueprint, request, jsonify
from models import db, Resource
from notifications import send_notification

resource_bp = Blueprint('resource', __name__)

@resource_bp.route('/request_resource', methods=['GET', 'POST'])
def request_resource():
    if request.method == 'POST':
        resource_type = request.form['resource_type']
        user_id = session.get('user_id')
        available_resources = Resource.query.filter_by(type=resource_type, status='available').all()
        assigned_resource = optimize_resource_allocation(available_resources)
        if assigned_resource:
            assigned_resource.status = 'occupied'
            db.session.commit()
            send_notification(user_id, f'Resource {assigned_resource.name} has been assigned to you.')
            flash('Resource assigned successfully!', 'success')
        else:
            flash('No resources available!', 'error')
        return redirect(url_for('resource.request_resource'))
    return render_template('request_resource.html')