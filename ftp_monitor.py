import os
from ftplib import FTP
import json
import urllib.request
import urllib.parse
from datetime import datetime

# הגדרות מתוך סביבת הריצה (GitHub Secrets)
FTP_HOST = os.environ.get("FTP_HOST")
FTP_USER = os.environ.get("FTP_USER")
FTP_PASS = os.environ.get("FTP_PASS")
FTP_DIR = os.environ.get("FTP_DIR", "/")  # תיקייה לבדיקה בשרת

PUSHOVER_TOKEN = os.environ.get("PUSHOVER_TOKEN")
PUSHOVER_USER = os.environ.get("PUSHOVER_USER")

# קובץ מעקב מקומי לשמירת מצב הקבצים האחרון
STATE_FILE = "ftp_state.json"


def send_pushover(message):
  """שולח הודעת התראה דרך Pushover"""
  if not PUSHOVER_TOKEN or not PUSHOVER_USER:
    print("Pushover credentials not set. Skipping notification.")
    return

  url = "https://api.pushover.net/1/messages.json"
  data = urllib.parse.urlencode({
      "token": PUSHOVER_TOKEN,
      "user": PUSHOVER_USER,
      "message": message,
      "title": "FTP Server Monitor",
  }).encode("utf-8")

  try:
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as response:
      if response.status == 200:
        print("Pushover notification sent successfully.")
      else:
        print(f"Failed to send Pushover notification: {response.status}")
  except Exception as e:
    print(f"Error sending Pushover notification: {e}")


def load_previous_state():
  """טוען את מצב הקבצים מהריצה הקודמת"""
  if os.path.exists(STATE_FILE):
    try:
      with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def save_current_state(state):
  """שומר את מצב הקבצים הנוכחי לקובץ"""
  with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)


def check_ftp():
  print(f"Connecting to FTP server: {FTP_HOST}...")
  ftp = FTP(FTP_HOST)
  ftp.login(user=FTP_USER, passwd=FTP_PASS)
  ftp.cwd(FTP_DIR)

  current_files = {}

  # שליפת רשימת הקבצים והמידע עליהם (תאריך עדכון/גודל)
  # פקודת MLSD מחזירה מידע מפורט (אם נתמך ע"י השרת), אחרת נשתמש ב-NLST/dir
  try:
    files_list = list(ftp.mlsd())
    for filename, facts in files_list:
      if filename in [".", ".."]:
        continue
      if facts.get("type") == "file":
        # שומרים את תאריך השינוי או הגודל כמזהה שינוי
        current_files[filename] = facts.get("modify", "") or facts.get(
            "size", ""
        )
  except Exception:
    # גיבוי במידה ו-MLSD לא נתמך בשרת
    print("MLSD not supported, falling back to basic directory listing...")
    lines = []
    ftp.retrlines('LIST', lines.။append if hasattr(lines, 'append') else None)
    # לצורך פשטות בסיסית אם אין MLSD, נשתמש במידע בסיסי
    for line in lines:
      parts = line.split()
      if parts:
        filename = parts[-1]
        current_files[filename] = line

  ftp.quit()

  # השוואה מול המצב הקודם
  previous_files = load_previous_state()

  if not previous_files:
    print("Initial run: saving current state without sending notifications.")
    save_current_state(current_files)
    return

  new_or_modified = []
  for filename, mtime in current_files.items():
    if filename not in previous_files:
      new_or_modified.append(f"נוסף קובץ חדש: {filename}")
    elif previous_files[filename] != mtime:
      print(previous_files[filename], mtime)
      new_or_modified.append(f"עודכן קובץ: {filename}")

  if new_or_modified:
    message = "\n".join(new_or_modified)
    print(f"Changes detected:\n{message}")
    send_pushover(message)
  else:
    print("No changes detected on FTP server.")

  # שמירת המצב החדש לקראת הריצה הבאה
  save_current_state(current_files)


if __name__ == "__main__":
  check_ftp()
