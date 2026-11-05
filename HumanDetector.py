import io
import os
import time
from ftplib import FTP
import cv2
import numpy as np
import requests

# --- CONFIGURATION (משתני סביבה מאובטחים) ---
FTP_HOST = os.getenv("FTP_HOST0", "yourserver.com")
FTP_USER = os.getenv("FTP_USER", "your_ftp_username")
FTP_PASS = os.getenv("FTP_PASS", "your_ftp_password")
# שינוי נתיב ברירת המחדל ליחסי (בלי / בהתחלה) כדי למנוע שגיאות 550 ברוב השרתים
FTP_FOLDER = os.getenv("FTP_FOLDER", "camera_uploads")  

PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "your_user_key_here")
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN", "your_app_token_here")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))  # בדיקה כל X שניות
LOCAL_ALERT_DIR = "./alerts"

os.makedirs(LOCAL_ALERT_DIR, exist_ok=True)


class FTPHumanDetector:

    def __init__(self):
        # Initialize OpenCV HOG person detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def send_pushover(self, message, image_data, filename):
        """Sends an alert to Pushover with an in-memory image buffer."""
        url = "https://api.pushover.net/1/messages.json"
        payload = {
            "token": PUSHOVER_APP_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": message,
        }
        files = {"attachment": (filename, image_data, "image/jpeg")}
        try:
            res = requests.post(url, data=payload, files=files)
            if res.status_code == 200:
                print("[✓] Pushover notification sent successfully.")
            else:
                print(f"[✗] Pushover error: {res.text}")
        except Exception as e:
            print(f"[✗] Failed to connect to Pushover: {e}")

    def process_image_buffer(self, file_bytes, filename):
        """Decodes image from memory, scans for humans, and handles alerts."""
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            print(f"[!] Could not decode image: {filename}")
            return

        # Scan for human bounding boxes
        boxes, _ = self.hog.detectMultiScale(
            img, winStride=(8, 8), padding=(8, 8), scale=1.05
        )

        if len(boxes) > 0:
            print(f"[!] Human detected in {filename}! Drawing bounding boxes...")
            for x, y, w, h in boxes:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # Save a local record of the alert image
            local_path = os.path.join(LOCAL_ALERT_DIR, f"alert_{filename}")
            cv2.imwrite(local_path, img)

            # Encode back to JPEG bytes to pass to Pushover API
            _, encoded_img = cv2.imencode(".jpg", img)
            img_bytes = io.BytesIO(encoded_img.tobytes())

            self.send_pushover(
                f"⚠️ Security Alert: Human detected on FTP camera feed ({filename})",
                img_bytes,
                filename,
            )
        else:
            print(f"[•] Scan clear for file: {filename}")

    def watch_ftp(self):
        """Main loop that continuously checks the FTP server."""
        print(f"[*] Starting FTP Monitor on {FTP_HOST}:{FTP_FOLDER}...")

        while True:
            try:
                # Establish connection
                ftp = FTP(FTP_HOST)
                ftp.login(user=FTP_USER, passwd=FTP_PASS)
                
                # מנגנון הגנה מפני שגיאת 550: ניסיון מעבר לתיקייה, ויצירה שלה אם היא חסרה
                try:
                    ftp.cwd(FTP_FOLDER)
                except Exception:
                    print(f"[!] Folder '{FTP_FOLDER}' not found. Attempting to create it...")
                    try:
                        ftp.mkd(FTP_FOLDER)
                        ftp.cwd(FTP_FOLDER)
                        print(f"[✓] Successfully created and moved to folder: {FTP_FOLDER}")
                    except Exception as create_err:
                        print(f"[✗] Failed to create folder: {create_err}")
                        raise

                # Get list of files
                files = []
                ftp.retrlines("NLST", files.append)

                # Filter for image extensions
                images = [
                    f
                    for f in files
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                ]

                for filename in images:
                    print(f"[+] Found new file on FTP: {filename}")

                    try:
                        # Download file directly into RAM buffer
                        file_buffer = io.BytesIO()
                        ftp.retrbinary(f"RETR {filename}", file_buffer.write)
                        file_bytes = file_buffer.getvalue()

                        # Process the downloaded bytes
                        self.process_image_buffer(file_bytes, filename)

                        # Delete the file from FTP so we don't scan it again next loop
                        ftp.delete(filename)
                        print(f"[+] Removed {filename} from FTP server.")
                    except Exception as file_err:
                        print(f"[✗] Error handling file {filename}: {file_err}")
                        # ממשיך לקובץ הבא גם אם קובץ ספציפי נכשל (למשל אם הוא עדיין נכתב ע"י המצלמה)
                        continue

                ftp.quit()

            except Exception as e:
                print(f"[✗] FTP Monitoring Error: {e}")

            # Sleep before polling again
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    detector = FTPHumanDetector()
    detector.watch_ftp()
