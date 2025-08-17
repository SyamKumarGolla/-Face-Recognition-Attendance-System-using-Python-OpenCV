from flask import Flask, render_template, session
from models import db
from auth import auth_bp
from attendance import attendance_bp
from resource_allocation import resource_bp
from admin import admin_bp
from notifications import send_notification

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_automation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy instance with the Flask app
db.init_app(app)

# Create the database tables (only needed once)
with app.app_context():
    db.create_all()
# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(resource_bp)
app.register_blueprint(admin_bp)
#app.register_blueprint(notifications_bp)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard.', 'error')
        return redirect(url_for('auth.login'))  # Ensure auth.login exists in auth.py
    print("Session Data:", session)  # Debugging: Print session data
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)