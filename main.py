import os
from ftplib import FTP
import requests

# טעינת משתני סביבה מה-Secrets של GitHub
FTP_HOST = os.environ.get('FTP_HOST')
FTP_USER = os.environ.get('FTP_USER', '')  # ברירת מחדל אנונימי אם ריק
FTP_PASS = os.environ.get('FTP_PASS', '')
PUSHOVER_USER = os.environ.get('PUSHOVER_USER_KEY')
PUSHOVER_TOKEN = os.environ.get('PUSHOVER_API_TOKEN')

CACHE_FILE = "ftp_snapshot.txt"

def send_pushover_notification(message):
    """פונקציה לשליחת התראה ל-Pushover"""
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        print("⚠️ פרטי Pushover חסרים, מדלג על שליחת התראה.")
        return
    
    url = "https://pushover.net"
    data = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": message,
        "title": "🔔 שינוי בשרת ה-FTP!"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("📱 התראה נשלחה בהצלחה ל-Pushover!")
    else:
        print(f"❌ שגיאה בשליחת התראה: {response.text}")

def get_ftp_files():
    """התחברות ל-FTP ושליפת רשימת הקבצים והתיקיות"""
    files = []
    print(f"🔄 מתחבר לשרת {FTP_HOST}...")
    with FTP(FTP_HOST) as ftp:
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        # שימוש בפקודת NLST כדי לקבל רשימה נקייה של שמות קבצים
        files = ftp.nlst()
    return sorted(files)

def main():
    try:
        # 1. קבלת רשימת הקבצים הנוכחית מה-FTP
        current_files = get_ftp_files()
        current_snapshot = "\n".join(current_files)
        
        # 2. בדיקה האם קיים מצב קודם (Cache)
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                previous_snapshot = f.read()
            
            # 3. השוואה בין המצב הקודם לנוכחי
            if current_snapshot != previous_snapshot:
                print("⚠️ נמצא שינוי בתיקייה!")
                
                previous_files = previous_snapshot.splitlines() if previous_snapshot else []
                
                # זיהוי מה השתנה
                added = [f for f in current_files if f not in previous_files]
                removed = [f for f in previous_files if f not in current_files]
                
                msg_parts = []
                if added:
                    msg_parts.append(f"➕ קבצים חדשים: {', '.join(added)}")
                if removed:
                    msg_parts.append(f"➖ קבצים שנמחקו: {', '.join(removed)}")
                
                full_message = "\n".join(msg_parts) if msg_parts else "חלו שינויים בתיקייה."
                send_pushover_notification(full_message)
            else:
                print("✅ אין שינוי בתיקייה מאז הריצה האחרונה.")
        else:
            print("ℹ️ ריצה ראשונה או שאין קובץ היסטוריה. שומר מצב ראשוני ומדלג על התראה.")

        # 4. שמירת המצב הנוכחי לריצה הבאה
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(current_snapshot)

    except Exception as e:
        print(f"❌ שגיאה בתהליך: {e}")

if __name__ == "__main__":
    main()
