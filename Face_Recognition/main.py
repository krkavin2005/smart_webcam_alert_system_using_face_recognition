import os, json, cv2, numpy as np, face_recognition
from alert_system import AlertManager
from db_manager import init_db,log_event
from utils import enhance_low_light,snapshots_dir

#Paths
ENCODINGS_FILE=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","Encoding","encodings.json"))

#load encodings
with open(ENCODINGS_FILE, "r") as f:
    data=json.load(f)
known_names=data["names"]
known_encodings=[np.array(e) for e in data["encodings"]]

#init db
init_db()
alert_mgr=AlertManager(cooldown_seconds=60)

# Performance optimization settings
FRAME_SKIP = 2  # Process every 2nd frame
SNAPSHOT_CONFIDENCE_THRESHOLD = 0.8  # Only save snapshots for high confidence matches
PROCESSING_SCALE = 0.25  # Scale factor for processing
frame_count = 0

# Store last detected faces for persistent display
last_detected_faces = []

def draw_persistent_faces(frame, faces_list):
    """Draw stored face boxes and labels on the frame"""
    for face_info in faces_list:
        left, top, right, bottom, name, confidence = face_info
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Add confidence display for known faces
        if name != "Unknown" and confidence > 0:
            cv2.putText(frame, f"{confidence:.2f}", (left, top-30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

cap=cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Camera not accessible")

print("[INFO] Starting optimized face recognition...")
print("[INFO] Processing every {} frame(s) for better performance".format(FRAME_SKIP + 1))

while True:
    ok,frame=cap.read()
    if not ok:
        print("[ERROR] Frame grab failed")
        break

    frame_count += 1

    # Skip frames for better performance
    if frame_count % (FRAME_SKIP + 1) != 0:
        # Draw persistent faces from last processed frame
        if last_detected_faces:
            draw_persistent_faces(frame, last_detected_faces)

        # Display frame with FPS info
        fps_text = f"FPS: {cap.get(cv2.CAP_PROP_FPS):.1f} | Frame: {frame_count}"
        cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Smart webcam alert (phase 5)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Only apply enhancement when needed (every few frames)
    if frame_count % 10 == 0:  # Check lighting every 10 processed frames
        enhanced=enhance_low_light(frame)
    else:
        enhanced = frame

    # Process at reduced scale for better performance
    small = cv2.resize(enhanced, (0,0),fx=PROCESSING_SCALE,fy=PROCESSING_SCALE)
    rgb_small=cv2.cvtColor(small,cv2.COLOR_BGR2RGB)

    # Detect faces
    locs = face_recognition.face_locations(rgb_small)

    # Only compute encodings if faces are detected
    if locs:
        encs=face_recognition.face_encodings(rgb_small,locs)

        # Clear previous faces and store new ones
        last_detected_faces.clear()

        for(face_top, face_right, face_bottom, face_left), enc in zip(locs, encs):
            # Batch face comparison for better performance
            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.4)  # Lower tolerance for better accuracy
            face_distances = face_recognition.face_distance(known_encodings, enc)

            name = "Unknown"
            confidence = 0.0
            MIN_CONFIDENCE_THRESHOLD = 0.3  # Minimum confidence to declare a match

            if True in matches:
                best_match_index = matches.index(True)
                confidence = 1.0 - face_distances[best_match_index]

                # Only declare a match if confidence is above threshold
                if confidence > MIN_CONFIDENCE_THRESHOLD:
                    name = known_names[best_match_index]
                else:
                    name = "Unknown"
                    confidence = 0.0

            # Scale coordinates back to original size
            # face_recognition returns (top, right, bottom, left) format
            orig_top = int(face_top * (1/PROCESSING_SCALE))
            orig_right = int(face_right * (1/PROCESSING_SCALE))
            orig_bottom = int(face_bottom * (1/PROCESSING_SCALE))
            orig_left = int(face_left * (1/PROCESSING_SCALE))

            # Store face info for persistent display
            last_detected_faces.append((orig_left, orig_top, orig_right, orig_bottom, name, confidence))

            # Choose color based on recognition
            if name != "Unknown":
                color = (0, 255, 0)  # Green for known faces
            else:
                color = (0, 0, 255)  # Red for unknown faces

            # Draw rectangle on enhanced frame
            cv2.rectangle(enhanced, (orig_left, orig_top), (orig_right, orig_bottom), color, 2)
            cv2.putText(enhanced, name, (orig_left, orig_top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Add confidence display for known faces
            if name != "Unknown" and confidence > 0:
                cv2.putText(enhanced, f"{confidence:.2f}", (orig_left, orig_top-30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Save snapshots for every detected face
            snaps = snapshots_dir()
            face_crop = frame[orig_top:orig_bottom, orig_left:orig_right]
            snap_path = None

            # Save snapshot for every detected face
            if face_crop.size > 0:
                snap_path = os.path.join(snaps, f"{name}_{orig_top}_{orig_right}_{frame_count}.jpg")
                cv2.imwrite(snap_path, face_crop)

            # Log events and send alerts
            if name == "Unknown":
                log_event(name, "intruder", snap_path)
                alert_mgr.alert_unknown(frame)
            else:
                log_event(name, "known", snap_path)

    # Display frame with FPS info
    fps_text = f"FPS: {cap.get(cv2.CAP_PROP_FPS):.1f} | Frame: {frame_count}"
    cv2.putText(enhanced, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("Smart webcam alert (phase 5)", enhanced)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("[INFO] Face recognition system stopped.")
