from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

# Firebase Initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceatten-95927-default-rtdb.firebaseio.com/"
})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/attendance', methods=['POST'])
def attendance():
    student_id = request.form['student_id']
    ref = db.reference(f'Students/{student_id}/Attendance')
    attendance_data = ref.get()

    if attendance_data:
        # Group attendance records by date
        attendance_by_date = {}
        for timestamp, status in attendance_data.items():
            date = timestamp.split(" ")[0]  # Extract date part (YYYY-MM-DD)
            if date not in attendance_by_date:
                attendance_by_date[date] = "Present"

        return render_template('attendance.html', student_id=student_id, attendance_data=attendance_by_date)
    else:
        return "No attendance records found for this student."

if __name__ == '__main__':
    app.run(debug=True)