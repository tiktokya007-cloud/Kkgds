import os
import ftplib
import requests

# הגדרת קובץ ה-Cache
CACHE_FILE = "seen_files_cache.txt"

# שליפת נתוני התחברות ממשתני הסביבה (Environment Variables)
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

def load_seen_files():
    """טעינת הקבצים שכבר ראינו מתוך קובץ ה-Cache"""
    try:
        with open(CACHE_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_seen_files(seen_files):
    """שמירת רשימת הקבצים חזרה לקובץ ה-Cache"""
    with open(CACHE_FILE, "w") as f:
        for filename in sorted(seen_files):
            f.write(f"{filename}\n")

def send_pushover_notification(filename):
    """שליחת התראה לפושאובר על קובץ חדש"""
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": f"קובץ חדש נמצא ב-FTP: {filename}"
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except Exception as e:
        print(f"שגיאה בשליחת התראה ל-Pushover: {e}")

def main():
    # 1. טעינת הקבצים שנקראו בעבר
    seen_files = load_seen_files()
    
    # 2. התחברות לשרת ה-FTP ושליפת רשימת הקבצים
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        current_files = ftp.nlst() # או רשימת הקבצים המלאה לפי הלוגיקה שלך
        ftp.quit()
    except Exception as e:
        print(f"שגיאה בהתחברות ל-FTP: {e}")
        return

    new_files_found = False

    # 3. מעבר על הקבצים ובדיקה האם הם חדשים
    for filename in current_files:
        # דילוג על תיקיות מערכת כמו . או .. אם רלוונטי
        if filename in [".", ".."]:
            continue
            
        if filename not in seen_files:
            print(f"נמצא קובץ חדש: {filename}")
            # שליחת התראה
            send_pushover_notification(filename)
            # הוספה לרשימת הנצפים
            seen_files.add(filename)
            new_files_found = True

    # 4. אם נמצאו קבצים חדשים, נשמור את הקובץ המעודכן
    if new_files_found:
        save_seen_files(seen_files)
        print("קובץ ה-Cache עודכן בהצלחה.")
    else:
        print("לא נמצאו קבצים חדשים.")

if __name__ == "__main__":
    main()
