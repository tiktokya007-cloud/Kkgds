import os
from ftplib import FTP
import requests
from datetime import datetime

# טעינת משתני סביבה מה-Secrets של GitHub
FTP_HOST = os.environ.get('FTP_HOST')
FTP_USER = os.environ.get('FTP_USER', '')  
FTP_PASS = os.environ.get('FTP_PASS', '')
PUSHOVER_USER = os.environ.get('PUSHOVER_USER_KEY')
PUSHOVER_TOKEN = os.environ.get('PUSHOVER_API_TOKEN')

CACHE_FILE = "seen_files_cache.txt"

def send_pushover_notification(message):
    """פונקציה לשליחת התראה ל-Pushover"""
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        print("⚠️ פרטי Pushover חסרים, מדלג על שליחת התראה.")
        return
     
    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": message,
        "title": "📸 תמונות חדשות ב-FTP"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("📱 התראה נשלחה בהצלחה ל-Pushover!")
    else:
        print(f"❌ שגיאה בשליחת התראה: {response.text}")

def get_ftp_files_from_dynamic_path():
    """התחברות ל-FTP, ניווט לתיקייה הדינמית ושליפת רשימת הקבצים"""
    now = datetime.utcnow()
    current_date = now.strftime("%Y-%m-%d")
    
    target_dir = f"/maintenance/192.168.1.246_00124275e927/{current_date}/04/pic"
    
    print(f"🔄 מתחבר לשרת {FTP_HOST}...")
    with FTP(FTP_HOST) as ftp:
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        
        try:
            print(f"📂 מנווט לתיקייה: {target_dir}")
            ftp.cwd(target_dir)
            files = ftp.nlst()
            return sorted(files), target_dir
        except Exception as e:
            print(f"ℹ️ התיקייה {target_dir} עדיין לא קיימת בשרת. שגיאה: {e}")
            return [], target_dir

def main():
    try:
        current_files, target_dir = get_ftp_files_from_dynamic_path()
        if not current_files:
            print("📭 התיקייה ריקה או לא קיימת, אין מה לנטר כרגע.")
            return

        # טעינת קבצים שכבר ראינו בעבר (מתוך הקאש)
        seen_files = set()
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                seen_files = set(line.strip() for line in f if line.strip())

        # أיתור קבצים חדשים לחלוטין שלא ראינו מעולם
        # נשמור גם את שם התיקייה יחד עם שם הקובץ כדי למנוע התנגשויות בין ימים/תיקיות שונים
        new_files = []
        for file in current_files:
            file_identifier = f"{target_dir}/{file}"
            if file_identifier not in seen_files:
                new_files.append(file)
                seen_files.add(file_identifier)

        if new_files:
            print(f"⚠️ נמצאו {len(new_files)} קבצים חדשים!")
            msg = f"➕ התווספו {len(new_files)} תמונות חדשות בנתיב:\n{target_dir}\n\nקבצים: {', '.join(new_files[:5])}"
            if len(new_files) > 5:
                msg += f" ועוד {len(new_files)-5} קבצים..."
            send_pushover_notification(msg)
        else:
            print("✅ אין קבצים חדשים מאז הבדיקה האחרונה.")

        # שמירת כל הקבצים שראינו עד כה בחזרה לקאש
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            for item in sorted(seen_files):
                f.write(f"{item}\n")

    except Exception as e:
        print(f"❌ שגיאה בתהליך: {e}")

if __name__ == "__main__":
    main()
