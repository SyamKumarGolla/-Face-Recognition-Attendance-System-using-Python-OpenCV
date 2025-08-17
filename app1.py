from flask import Flask, request, jsonify, render_template
import sqlite3
import datetime

app = Flask(__name__)


# ---------------------------
# Database helper functions
# ---------------------------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create table for resources
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resources (
       id INTEGER PRIMARY KEY,
       resource_type TEXT NOT NULL,
       resource_name TEXT NOT NULL,
       available INTEGER NOT NULL
    );
    ''')
    # Table for resource allocation requests
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resource_requests (
       id INTEGER PRIMARY KEY,
       user TEXT NOT NULL,
       resource_type TEXT NOT NULL,
       requested_time TEXT NOT NULL,
       request_status TEXT NOT NULL,
       allocated_resource_id INTEGER,
       timestamp TEXT NOT NULL
    );
    ''')
    # Table for logging allocation history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS allocation_history (
       id INTEGER PRIMARY KEY,
       request_id INTEGER NOT NULL,
       allocated_resource_id INTEGER,
       allocation_time TEXT NOT NULL,
       status TEXT NOT NULL
    );
    ''')
    # Insert some sample resources if none exist
    cursor.execute("SELECT COUNT(*) FROM resources")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_resources = [
            ('Classroom', 'Room 101', 1),
            ('Classroom', 'Room 102', 1),
            ('Lab', 'Computer Lab 1', 1),
            ('Equipment', 'Projector 1', 1),
            ('Equipment', 'Projector 2', 1),
            ('Staff', 'Technician 1', 1)
        ]
        cursor.executemany(
            "INSERT INTO resources (resource_type, resource_name, available) VALUES (?, ?, ?)",
            sample_resources
        )
    conn.commit()
    conn.close()


# ---------------------------
# Notification simulation
# ---------------------------
def notify_user(user, message):
    print(f"Notification for {user}: {message}")


# ---------------------------
# AI-Based Optimization Function
# ---------------------------
def assign_best_resource(resource_type, requested_time):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM resources WHERE resource_type = ? AND available = 1 LIMIT 1",
        (resource_type,)
    )
    resource = cursor.fetchone()
    conn.close()
    return resource


# ---------------------------
# Frontend Route
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------
# API Endpoints for Resource Allocation
# ---------------------------
@app.route("/request", methods=["POST"])
def create_request():
    data = request.json
    user = data.get("user")
    resource_type = data.get("resource_type")
    requested_time = data.get("requested_time")

    if not user or not resource_type or not requested_time:
        return jsonify({"error": "Missing required fields: user, resource_type, requested_time"}), 400

    timestamp = datetime.datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO resource_requests (user, resource_type, requested_time, request_status, allocated_resource_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user, resource_type, requested_time, "pending", None, timestamp))
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"message": "Resource request created", "request_id": request_id})


@app.route("/availability", methods=["GET"])
def fetch_availability():
    resource_type = request.args.get("resource_type")
    if not resource_type:
        return jsonify({"error": "resource_type query parameter is required"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resources WHERE resource_type = ? AND available = 1", (resource_type,))
    resources = cursor.fetchall()
    conn.close()
    resources_list = [dict(r) for r in resources]

    return jsonify({"available_resources": resources_list})


@app.route("/allocate", methods=["POST"])
def allocate_resource():
    data = request.json
    request_id = data.get("request_id")
    if not request_id:
        return jsonify({"error": "Missing 'request_id' in payload"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    # Retrieve the pending request
    cursor.execute("SELECT * FROM resource_requests WHERE id = ?", (request_id,))
    r_request = cursor.fetchone()
    if not r_request:
        conn.close()
        return jsonify({"error": "Resource request not found"}), 404
    if r_request["request_status"] != "pending":
        conn.close()
        return jsonify({"error": "This resource request has already been processed."}), 400

    resource_type = r_request["resource_type"]
    requested_time = r_request["requested_time"]

    best_resource = assign_best_resource(resource_type, requested_time)
    if not best_resource:
        conn.close()
        return jsonify({"error": f"No available resource found for {resource_type}"}), 404

    cursor.execute("""
         UPDATE resource_requests 
         SET request_status = ?, allocated_resource_id = ?
         WHERE id = ?
         """, ("allocated", best_resource["id"], request_id))

    cursor.execute("UPDATE resources SET available = 0 WHERE id = ?", (best_resource["id"],))

    allocation_time = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO allocation_history (request_id, allocated_resource_id, allocation_time, status)
        VALUES (?, ?, ?, ?)
    ''', (request_id, best_resource["id"], allocation_time, "allocated"))

    conn.commit()
    conn.close()

    notify_user(r_request["user"],
                f"Your resource request (ID: {request_id}) has been allocated to {best_resource['resource_name']} (Pending admin approval).")

    return jsonify({
        "message": f"Resource allocated: {best_resource['resource_name']}",
        "request_id": request_id,
        "allocated_resource": dict(best_resource)
    })


@app.route("/admin/approve", methods=["POST"])
def admin_approval():
    data = request.json
    request_id = data.get("request_id")
    action = data.get("action")

    if not request_id or action not in ["approve", "reject"]:
        return jsonify({"error": "Missing request_id or invalid action. Action must be 'approve' or 'reject'."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM resource_requests WHERE id = ?", (request_id,))
    r_request = cursor.fetchone()
    if not r_request:
        conn.close()
        return jsonify({"error": "Resource request not found"}), 404
    if r_request["request_status"] != "allocated":
        conn.close()
        return jsonify({"error": "Only allocated requests can be approved or rejected."}), 400

    allocated_resource_id = r_request["allocated_resource_id"]

    if action == "approve":
        new_status = "approved"
        cursor.execute("UPDATE resource_requests SET request_status = ? WHERE id = ?", (new_status, request_id))
        cursor.execute("UPDATE allocation_history SET status = ? WHERE request_id = ?", (new_status, request_id))
        notify_user(r_request["user"], f"Your resource request (ID: {request_id}) has been APPROVED.")
    else:
        new_status = "rejected"
        cursor.execute("UPDATE resource_requests SET request_status = ? WHERE id = ?", (new_status, request_id))
        cursor.execute("UPDATE allocation_history SET status = ? WHERE request_id = ?", (new_status, request_id))
        cursor.execute("UPDATE resources SET available = 1 WHERE id = ?", (allocated_resource_id,))
        notify_user(r_request["user"], f"Your resource request (ID: {request_id}) has been REJECTED.")

    conn.commit()
    conn.close()

    return jsonify({"message": f"Resource request {request_id} has been {new_status} by Admin."})


@app.route("/dashboard", methods=["GET"])
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM resource_requests")
    requests = cursor.fetchall()

    cursor.execute("SELECT * FROM allocation_history")
    history = cursor.fetchall()

    conn.close()

    return jsonify({
        "resource_requests": [dict(r) for r in requests],
        "allocation_history": [dict(h) for h in history]
    })


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "Resource Allocation Module is running fine."})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
