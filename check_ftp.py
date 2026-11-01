import os
import sys
import json
import ftplib
import requests

# טעינת משתני סביבה (הגדרות מאובטחות)
FTP_HOST = os.environ.get("FTP_HOST")
FTP_USER = os.environ.get("FTP_USER")
FTP_PASS = os.environ.get("FTP_PASS")
FTP_DIR = os.environ.get("FTP_DIR", "/")
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")

STATE_FILE = "ftp_state.json"

def get_ftp_files():
    """מתחבר ל-FTP ומחזיר רשימה של קבצים והגודל שלהם."""
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd(FTP_DIR)
        
        files = {}
        # שליפת רשימת קבצים עם פרטים
        lines = []
        ftp.retrlines('LIST', lines.append)
        
        for line in lines:
            parts = line.split(None, 8)
            if len(parts) >= 9:
                filename = parts[-1]
                # התעלמות מתיקיות נוכחיות/אב
                if filename in [".", ".."]:
                    continue
                # בדיקה אם זו תיקייה (לפי הסימן הראשון ב-Unix LIST)
                is_dir = parts[0].startswith('d')
                if not is_dir:
                    size = parts[4]
                    files[filename] = size
        
        ftp.quit()
        return files
    except Exception as e:
        print(f"שגיאה בהתחברות ל-FTP: {e}")
        sys.exit(1)

def send_pushover(message):
    """שולח התראה ל-Pushover."""
    url = "https://pushover.net"
    data = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "title": "עדכון שרת FTP",
        "message": message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("ההתראה נשלחה בהצלחה ל-Pushover.")
    else:
        print(f"שגיאה בשליחת התראה: {response.text}")

def main():
    # קריאת המצב הקודם אם קיים
    old_state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            old_state = json.load(f)

    # שליפת המצב הנוכחי מהשרת
    current_state = get_ftp_files()

    # זיהוי שינויים
    added = [f for f in current_state if f not in old_state]
    removed = [f for f in old_state if f not in current_state]
    modified = [f for f in current_state if f in old_state and current_state[f] != old_state[f]]

    # בניית הודעה
    messages = []
    if added:
        messages.append(f"🆕 קבצים חדשים: {', '.join(added)}")
    if modified:
        messages.append(f"✏️ קבצים ששונו: {', '.join(modified)}")
    if removed:
        messages.append(f"❌ קבצים שנמחקו: {', '.join(removed)}")

    if messages:
        full_message = "\n".join(messages)
        print("נמצאו שינויים:\n", full_message)
        send_pushover(full_message)
    else:
        print("לא נמצאו שינויים בשרת ה-FTP.")

    # שמירת המצב הנוכחי לריצה הבאה
    with open(STATE_FILE, "w") as f:
        json.load = json.dump(current_state, f)

if __name__ == "__main__":
    main()
