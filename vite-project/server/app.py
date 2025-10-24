from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os, pandas as pd, shutil, json
from flask_cors import CORS
import face_recognition, cv2
import numpy as np

app = Flask(__name__)
CORS(app)

# === PATH SETUP ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # vite-project/server
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # Mini Project root

DB_FILE = os.path.join(PROJECT_ROOT, "Logs", "intruder_log.db")
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "alerts", "snapshots")
DATASET_DIR = os.path.join(PROJECT_ROOT, "dataset")
ENCODINGS_FILE = os.path.join(PROJECT_ROOT, "Encoding", "encodings.json")

print("🗂 Database file:", DB_FILE)
print("📸 Snapshot dir:", SNAPSHOT_DIR)
print("🧠 Dataset dir:", DATASET_DIR)
print("💾 Encodings file:", ENCODINGS_FILE)


# === ENCODING UTILITIES ===
def load_encodings():
    """Load existing encodings or return empty structure."""
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Corrupted encodings file. Resetting.")
                return {"names": [], "encodings": []}
    return {"names": [], "encodings": []}


def save_encodings(data):
    """Save encodings JSON."""
    with open(ENCODINGS_FILE, "w") as f:
        json.dump(data, f)


def add_encoding_for_image(image_path, name):
    """Detect faces, extract encoding, and append to encodings.json."""
    if not os.path.exists(image_path):
        print(f"❌ Encoding failed: image not found - {image_path}")
        return False

    try:
        image = cv2.imread(image_path)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        encs = face_recognition.face_encodings(rgb, boxes)

        if not encs:
            print(f"⚠️ No face detected in {image_path}")
            return False

        data = load_encodings()
        data["names"].append(name)
        data["encodings"].append(encs[0].tolist())
        save_encodings(data)

        print(f"✅ Added encoding for {name}")
        return True

    except Exception as e:
        print(f"❌ Encoding error for {name}: {e}")
        return False


# === DATABASE UTIL ===
def fetch_logs():
    """Read intruder logs and attach snapshot URLs."""
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError(f"Database not found at {DB_FILE}")

    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY timestamp DESC", conn)
    conn.close()

    df["snapshot_url"] = df["snapshot"].apply(
        lambda x: f"http://127.0.0.1:5000/snapshots/{os.path.basename(x)}"
        if x and os.path.exists(x)
        else None
    )
    return df


# === ROUTES ===
@app.route("/api/logs", methods=["GET"])
def get_logs():
    df = fetch_logs()
    return jsonify(df.to_dict(orient="records"))


@app.route("/snapshots/<path:filename>")
def serve_snapshot(filename):
    return send_from_directory(SNAPSHOT_DIR, filename)


# === ADD KNOWN FACE ===
@app.route("/api/add_known", methods=["POST"])
def add_known():
    data = request.json
    id_, name = data.get("id"), data.get("name")

    if not name:
        return jsonify({"status": "error", "msg": "Name missing"})

    # Fetch snapshot path from DB
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT snapshot FROM logs WHERE id=?", (id_,))
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return jsonify({"status": "error", "msg": "Snapshot not found"})

    src_path = row[0]
    if not os.path.exists(src_path):
        print("⚠️ Snapshot path invalid. Attempting fix.")
        base_name = os.path.basename(src_path)
        fixed_path = os.path.join(SNAPSHOT_DIR, base_name)
        if os.path.exists(fixed_path):
            src_path = fixed_path
        else:
            return jsonify({"status": "error", "msg": "Snapshot file missing"})

    # Copy snapshot to dataset
    person_folder = os.path.join(DATASET_DIR, name)
    os.makedirs(person_folder, exist_ok=True)
    dest_path = os.path.join(person_folder, os.path.basename(src_path))
    shutil.copy(src_path, dest_path)

    # Add encoding
    add_encoding_for_image(dest_path, name)

    print(f"✅ Added known: {name}, snapshot copied to {person_folder}")
    return jsonify({"status": "ok", "msg": f"Added {name} to dataset"})


# === ADD UNKNOWN FACE (rename + encode) ===
@app.route("/api/add_unknown", methods=["POST"])
def add_unknown():
    data = request.json
    id_ = data.get("id")
    new_name = data.get("name")

    print(f"🕵️ Received add_unknown -> id={id_}, new_name={new_name}")

    # Lookup snapshot path from DB
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT snapshot FROM logs WHERE id=?", (id_,))
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return jsonify({"status": "error", "msg": "Snapshot not found in DB"})

    snapshot_path = row[0]
    base_name = os.path.basename(snapshot_path)

    # Fix path if not found
    if not os.path.exists(snapshot_path):
        snapshot_path = os.path.join(SNAPSHOT_DIR, base_name)
        if not os.path.exists(snapshot_path):
            return jsonify({"status": "error", "msg": "Snapshot file missing"})

    # Copy to dataset
    person_folder = os.path.join(DATASET_DIR, new_name.strip())
    os.makedirs(person_folder, exist_ok=True)
    dest_path = os.path.join(person_folder, base_name)
    shutil.copy(snapshot_path, dest_path)
    print(f"✅ Copied snapshot to dataset: {dest_path}")

    # Add encoding for the new person
    success = add_encoding_for_image(dest_path, new_name)
    if not success:
        return jsonify({"status": "warning", "msg": "Image copied but no face detected."})

    print(f"✅ Added unknown -> {new_name} encoded successfully")
    return jsonify({"status": "ok", "msg": f"{new_name} added to dataset and encodings"})


# === MAIN ===
if __name__ == "__main__":
    app.run(debug=True)
