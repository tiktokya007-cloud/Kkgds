import ftplib
import os
import requests

# הגדרת משתני סביבה (יימשכו מתוך GitHub Secrets)
FTP_HOST = os.environ.get("FTP_HOST")
FTP_USER = os.environ.get("FTP_USER")
FTP_PASS = os.environ.get("FTP_PASS")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")

STATE_FILE = "ftp_state.txt"


def get_ftp_files():
    """מתחבר לשרת ה-FTP ומחזיר רשימת קבצים"""
    try:
        with ftplib.FTP(FTP_HOST) as ftp:
            ftp.login(user=FTP_USER, passwd=FTP_PASS)
            # החלף לתיקייה הרצויה בשרת במידת הצורך (למשל: ftp.cwd('/path'))
            files = ftp.nlst()
            return set(files)
    except Exception as e:
        print(f"Error connecting to FTP: {e}")
        return None


def send_pushover_notification(message):
    """שולח התראה ל-Pushover"""
    url = "https://pushover.net"
    data = {"token": PUSHOVER_TOKEN, "user": PUSHOVER_USER, "message": message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Notification sent successfully.")
    else:
        print(f"Failed to send notification: {response.text}")


def main():
    current_files = get_ftp_files()
    if current_files is None:
        return

    # קריאת המצב הקודם אם קיים
    previous_files = set()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            previous_files = set(line.strip() for line in f.readlines())

    # בדיקה האם יש קבצים חדשים
    new_files = current_files - previous_files

    if new_files:
        message = f"🔔 קבצים חדשים התגלו בשרת ה-FTP:\n" + "\n".join(new_files)
        print(message)
        send_pushover_notification(message)
    else:
        print("No new files detected.")

    # שמירת המצב הנוכחי לריצה הבאה
    with open(STATE_FILE, "w") as f:
        for file in current_files:
            f.write(f"{file}\n")


if __name__ == "__main__":
    main()
