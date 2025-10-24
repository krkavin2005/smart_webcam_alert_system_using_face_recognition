import streamlit as st
import sqlite3
import pandas as pd
import os
import shutil
import json
import face_recognition
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "Logs", "intruder_log.db"))
DATASET_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "dataset"))
ENCODINGS_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "Encoding", "encodings.json"))

st.title("Security Dashboard - Smart Webcam")
st.caption("Recent recognitions and alerts")

conn = sqlite3.connect(DB_FILE)
df = pd.read_sql_query("SELECT * FROM logs ORDER BY timestamp DESC", conn)
conn.close()
st.dataframe(df, use_container_width=True)
st.subheader("Latest snapshots")

if "show_name_inputs" not in st.session_state:
    st.session_state.show_name_inputs = {}

def load_encodings():
    """Load encodings.json safely and flatten if needed."""
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "r") as f:
            data = json.load(f)
            encodings_fixed = []
            for enc_list in data.get("encodings", []):
                if enc_list and isinstance(enc_list[0], list):
                    encodings_fixed.append(enc_list)
                else:
                    encodings_fixed.append([enc_list])
            return {"names": data.get("names", []), "encodings": encodings_fixed}
    else:
        return {"names": [], "encodings": []}

def save_encodings(data):
    """Save encodings to JSON."""
    with open(ENCODINGS_FILE, "w") as f:
        json.dump(data, f)

def get_known_encodings():
    """Return a flat list of np.array encodings for comparison."""
    data = load_encodings()
    known_encodings = []
    for person_encs in data["encodings"]:
        for enc in person_encs:
            known_encodings.append(np.array(enc))
    return known_encodings, data["names"]

for _, row in df.head(10).iterrows():
    if row["snapshot"] and os.path.exists(row["snapshot"]):
        st.image(
            row["snapshot"],
            caption=f'{row["status"]}: {row["name"]} @ {row["timestamp"]}',
            width=360,
        )

        with st.expander(f"Promote this snapshot ({row['timestamp']})"):

            if row["name"] != "Unknown":
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Add to Dataset", key=f"btn_known_{row['id']}"):
                        person_folder = os.path.join(DATASET_DIR, row["name"].strip())
                        os.makedirs(person_folder, exist_ok=True)

                        dest_path = os.path.join(person_folder, f"{row['name']}_{row['id']}.jpg")
                        shutil.copy(row["snapshot"], dest_path)

                        image = cv2.imread(row["snapshot"])
                        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        encs = face_recognition.face_encodings(rgb)

                        if encs:
                            data = load_encodings()
                            if row["name"] not in data["names"]:
                                data["names"].append(row["name"])
                                data["encodings"].append([encs[0].tolist()])
                            else:
                                idx = data["names"].index(row["name"])
                                data["encodings"][idx].append(encs[0].tolist())

                            save_encodings(data)
                            st.success(f"✅ Added snapshot & encoding for {row['name']}")

                with col2:
                    if st.button("Add Encoding Only", key=f"btn_encoding_{row['id']}"):
                        image = cv2.imread(row["snapshot"])
                        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        encs = face_recognition.face_encodings(rgb)

                        if encs:
                            data = load_encodings()
                            if row["name"] not in data["names"]:
                                data["names"].append(row["name"])
                                data["encodings"].append([encs[0].tolist()])
                            else:
                                idx = data["names"].index(row["name"])
                                data["encodings"][idx].append(encs[0].tolist())

                            save_encodings(data)
                            st.success(f"✅ Added additional encoding for {row['name']}")

            # Case 2: Unknown Face → Ask for name
            else:
                if st.button("Add to Known Faces", key=f"btn_unknown_{row['id']}"):
                    st.session_state.show_name_inputs[row["id"]] = True

                if st.session_state.show_name_inputs.get(row["id"], False):
                    # Use a session_state key for text_input
                    name_key = f"unknown_name_{row['id']}"
                    if name_key not in st.session_state:
                        st.session_state[name_key] = ""

                    # text_input automatically stores its value in st.session_state[name_key]
                    new_name = st.text_input(
                        "Enter name for this person:",
                        value=st.session_state[name_key],
                        key=name_key
                    )

                    if st.button("Save Unknown", key=f"save_unknown_{row['id']}"):
                        if new_name.strip():
                            person_folder = os.path.join(DATASET_DIR, new_name.strip())
                            os.makedirs(person_folder, exist_ok=True)

                            dest_path = os.path.join(person_folder, f"{new_name}_{row['id']}.jpg")
                            shutil.copy(row["snapshot"], dest_path)

                            image = cv2.imread(row["snapshot"])
                            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            encs = face_recognition.face_encodings(rgb)

                            if encs:
                                data = load_encodings()
                                if new_name.strip() not in data["names"]:
                                    data["names"].append(new_name.strip())
                                    data["encodings"].append([encs[0].tolist()])
                                else:
                                    idx = data["names"].index(new_name.strip())
                                    data["encodings"][idx].append(encs[0].tolist())

                                save_encodings(data)
                                st.success(f"✅ {new_name} promoted to dataset/{new_name}")

                                # Reset input and hide input box after saving
                                st.session_state[name_key] = ""
                                st.session_state.show_name_inputs[row["id"]] = False
                        else:
                            st.error("⚠️ Please enter a valid name")
