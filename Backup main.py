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

CACHE_FILE = "ftp_snapshot.txt"

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
    
    # הפקת התאריך והשעה הנוכחיים לפי הפורמט בנתיב שלך
    now = datetime.utcnow() # GitHub Actions רץ לפי שעון UTC
    current_date = now.strftime("%Y-%m-%d") # לדוגמה: 2026-11-01
    current_hour = now.strftime("%H")       # לדוגמה: 21
    
    # בניית הנתיב הדינמי בצורה אוטומטית
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
            # אם התיקייה עדיין לא נוצרה בשעה הזו על ידי המכשיר, נתפוס את השגיאה בעדינות
            print(f"ℹ️ התיקייה {target_dir} עדיין לא קיימת בשרת. שגיאה: {e}")
            return [], target_dir

def main():
    try:
        # 1. קבלת רשימת הקבצים מהנתיב הדינמי
        current_files, target_dir = get_ftp_files_from_dynamic_path()
        if not current_files:
            print("📭 התיקייה ריקה או לא קיימת, אין מה לנטר כרגע.")
            return

        current_snapshot = "\n".join(current_files)
        
        # 2. בדיקה האם קיים מצב קודם (Cache)
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                previous_snapshot = f.read()
            
            # 3. השוואה בין המצב הקודם לנוכחי
            if current_snapshot != previous_snapshot:
                print("⚠️ נמצא שינוי בתיקייה!")
                
                previous_files = previous_snapshot.splitlines() if previous_snapshot else []
                added = [f for f in current_files if f not in previous_files]
                
                if added:
                    msg = f"➕ התווספו {len(added)} תמונות חדשות בנתיב:\n{target_dir}\n\nקבצים: {', '.join(added[:5])}"
                    if len(added) > 5:
                        msg += f" ועוד {len(added)-5} קבצים..."
                    send_pushover_notification(msg)
            else:
                print("✅ אין שינוי בקבצים מאז הבדיקה האחרונה.")
        else:
            print("ℹ️ ריצה ראשונה בשעה זו. שומר מצב ראשוני ומדלג על התראה.")

        # 4. שמירת המצב הנוכחי לריצה הבאה
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(current_snapshot)

    except Exception as e:
        print(f"❌ שגיאה בתהליך: {e}")

if __name__ == "__main__":
    main()
