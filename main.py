import os
from ftplib import FTP

# GitHub Actions יזריק את המשתנה הזה ישירות לסביבת הריצה
FTP_HOST = os.environ.get('FTP_HOST')

if not FTP_HOST:
    raise ValueError("Missing FTP_HOST environment variable!")

try:
    print(f"Connecting to {FTP_HOST} via GitHub Actions...")
    with FTP(FTP_HOST) as ftp:
        ftp.login()  # אם יש משתמש וסיסמה: ftp.login(os.environ.get('FTP_USER'), os.environ.get('FTP_PASS'))
        print("Successfully connected from GitHub!")
        ftp.retrlines('LIST')
except Exception as e:
    print(f"Connection failed: {e}")
