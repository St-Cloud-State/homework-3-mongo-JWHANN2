from flask import Flask, render_template, request
from mongita import MongitaClientDisk
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)

client = MongitaClientDisk()
db = client.loan_db
applications = db.applications

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        zipcode = request.form["zipcode"]
        app_id = applications.insert_one({
            "name": name,
            "zipcode": zipcode,
            "status": "received",
            "notes": []
        }).inserted_id
        return render_template("confirmation.html", app_id=app_id)
    return render_template("index.html")

@app.route("/status", methods=["GET", "POST"])
def check_status():
    status = None
    notes = []
    if request.method == "POST":
        app_id = request.form["app_id"]
        try:
            app_data = applications.find_one({"_id": ObjectId(app_id)})
            if app_data:
                status = app_data["status"]
                notes = app_data.get("notes", [])
            else:
                status = "not found"
        except:
            status = "invalid ID"
    return render_template("status.html", status=status, notes=notes)

@app.route("/update", methods=["GET", "POST"])
def update():
    message = ""
    if request.method == "POST":
        app_id = request.form["app_id"]
        new_status = request.form["new_status"]
        subphase = request.form.get("subphase", "")
        note_msg = request.form.get("note", "")
        note_type = "generic"
        try:
            update_doc = {"status": new_status}
            note_entry = None

            if new_status == "rejected":
                if not note_msg.strip():
                    return render_template("update.html", message="Rejection reason is required.")
                note_type = "rejection_reason"

            elif new_status == "accepted":
                if note_msg.strip():
                    note_type = "loan_term"

            elif new_status == "processing":
                if note_msg.strip():
                    note_type = subphase if subphase else "processing"

            if note_msg.strip():
                note_entry = {
                    "type": note_type,
                    "message": note_msg.strip(),
                    "timestamp": datetime.utcnow().isoformat()
                }

            update_ops = {"$set": update_doc}
            if note_entry:
                update_ops["$push"] = {"notes": note_entry}

            result = applications.update_one({"_id": ObjectId(app_id)}, update_ops)

            if result.matched_count > 0:
                message = "Application updated successfully."
            else:
                message = "Application not found."
        except:
            message = "Invalid ID format."
    return render_template("update.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)

