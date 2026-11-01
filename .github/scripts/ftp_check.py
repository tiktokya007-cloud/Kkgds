import os
from ftplib import FTP
import http.client
import urllib.parse

# 1. טעינת משתני סביבה (מה-Secrets של GitHub או מהמערכת)
FTP_HOST = os.environ.get('FTP_HOST')
FTP_USER = os.environ.get('FTP_USER', '')
FTP_PASS = os.environ.get('FTP_PASS', '')

PUSHOVER_TOKEN = os.environ.get('PUSHOVER_TOKEN', '')
PUSHOVER_USER = os.environ.get('PUSHOVER_USER', '')

def send_pushover_notification(message):
    """פונקציה לשליחת התראה ל-Pushover"""
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        print("Pushover credentials not found, skipping notification.")
        return

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message,
        }), { "Content-type": "application/x-www-form-urlencoded" })
    
    response = conn.getresponse()
    if response.status == 200:
        print("Pushover notification sent successfully.")
    else:
        print(f"Failed to send Pushover notification: {response.status}")

def main():
    if not FTP_HOST:
        raise ValueError("שגיאה: משתנה הסביבה FTP_HOST אינו מוגדר!")

    try:
        print(f"מתחבר לשרת ה-FTP: {FTP_HOST}...")
        
        # יצירת חיבור והתחברות לשרת
        ftp = FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        
        print("התחברות ל-FTP הצליחה!")
        
        # שליחת התראה ל-Pushover ברגע שהחיבור הצליח
        send_pushover_notification(f"Success! Connected to FTP server: {FTP_HOST}")

        # סגירת החיבור בצורה מסודרת
        ftp.quit()

    except Exception as e:
        error_msg = f"שגיאה בהתחברות ל-FTP: {e}"
        print(error_msg)
        # אופציונלי: שליחת התראה גם במקרה של כישלון
        send_pushover_notification(error_msg)
        raise e

if __name__ == "__main__":
    main()
