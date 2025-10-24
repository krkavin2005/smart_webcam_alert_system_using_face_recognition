import face_recognition
import cv2
import os
import json
import numpy as np

# Dataset folder
DATASET_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset"))
ENCODINGS_FILE = "encodings.json"

known_encodings = []
known_names = []

print("[INFO] Starting encoding process...")

# Loop over each person in dataset
for person_name in os.listdir(DATASET_DIR):
    person_folder = os.path.join(DATASET_DIR, person_name)

    if not os.path.isdir(person_folder):
        continue

    print(f"[INFO] Processing: {person_name}")

    person_encodings = []

    # Loop over each image for this person
    for image_name in os.listdir(person_folder):
        image_path = os.path.join(person_folder, image_name)

        image = cv2.imread(image_path)
        if image is None:
            print(f"[WARNING] Could not read image {image_path}")
            continue

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces
        boxes = face_recognition.face_locations(rgb_image, model="hog")
        encodings = face_recognition.face_encodings(rgb_image, boxes)

        if encodings:
            person_encodings.extend(encodings)

    # Average all encodings for this person
    if person_encodings:
        avg_encoding = np.mean(person_encodings, axis=0)
        known_encodings.append(avg_encoding.tolist())
        known_names.append(person_name)

# Save single encoding per person
data = {"names": known_names, "encodings": known_encodings}

with open(ENCODINGS_FILE, "w") as f:
    json.dump(data, f)

print(f"[INFO] Encodings saved to {ENCODINGS_FILE}")
