import os
import json
import time
import smtplib
from email.message import EmailMessage

# === Config loading helpers ===
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMAIL_CFG = load_json(os.path.join(BASE_DIR,"Config", "email_config.json"))

# === Email alert ===
def send_email_alert(subject: str, body: str, image_path: str):
    """Send an email with an attached image. Uses SMTP over SSL (port 465)."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_CFG["sender_email"]
    msg["To"] = EMAIL_CFG["receiver_email"]
    msg.set_content(body)

    # Attach image
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img:
            img_data = img.read()
        maintype = "image"
        subtype = os.path.splitext(image_path)[1].replace(".", "").lower() or "jpeg"
        msg.add_attachment(img_data, maintype=maintype, subtype=subtype, filename=os.path.basename(image_path))

    try:
        with smtplib.SMTP_SSL(EMAIL_CFG["smtp_server"], EMAIL_CFG["smtp_port"]) as server:
            server.login(EMAIL_CFG["sender_email"], EMAIL_CFG["sender_password"])
            server.send_message(msg)
        print("[INFO] Email alert sent.")
        return True
    except Exception as e:
        print("[ERROR] Failed to send email:", e)
        return False


# === High-level combined alert with cooldown ===
class AlertManager:
    def __init__(self, cooldown_seconds=60):
        self.last_alert_time = 0
        self.cooldown_seconds = cooldown_seconds
        self.snapshots_dir = os.path.join(os.path.dirname(BASE_DIR), "alerts", "snapshots")
        os.makedirs(self.snapshots_dir, exist_ok=True)

    def can_alert(self):
        return (time.time() - self.last_alert_time) > self.cooldown_seconds

    def make_snapshot_path(self):
        ts = time.strftime("%Y%m%d_%H%M%S")
        filename = f"unknown_{ts}.jpg"
        return os.path.join(self.snapshots_dir, filename)

    def alert_unknown(self, frame):
        """
        frame: BGR image (numpy array) — will be saved as JPEG snapshot.
        """
        if not self.can_alert():
            print("[INFO] In cooldown period — not sending alert.")
            return False

        # Save snapshot
        path = self.make_snapshot_path()
        try:
            import cv2
            cv2.imwrite(path, frame)
        except Exception as e:
            print("[ERROR] Failed to save snapshot:", e)
            path = None

        # Compose messages
        subject = "Security Alert: Unknown person detected"
        body = "An unknown person was detected by the webcam. See attached image."

        email_ok = send_email_alert(subject, body, path)

        if email_ok:
            self.last_alert_time = time.time()
            return True

        return False
