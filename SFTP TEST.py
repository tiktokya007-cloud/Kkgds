import os
import json
import ftplib
import urllib.request
import urllib.parse

STATE_FILE = ".watcher_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_state(seen_files):
    with open(STATE_FILE, 'w') as f:
        json.dump(list(seen_files), f)

def send_pushover_notification(message):
    user_key = os.environ.get("PUSHOVER_USER_KEY")
    api_token = os.environ.get("PUSHOVER_API_TOKEN")
    
    if not user_key or not api_token:
        print("[!] Pushover configuration missing. Skipping notification.")
        return

    url = "https://api.pushover.net/1/messages.json"
    data = urllib.parse.urlencode({
        "token": api_token,
        "user": user_key,
        "message": message,
        "title": "FTP Watcher"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("[+] Pushover notification sent successfully.")
            else:
                print(f"[!] Pushover returned status code: {response.status}")
    except Exception as e:
        print(f"[!] Failed to send Pushover notification: {e}")

def watch_ftp_folder():
    host = os.environ.get('FTP_HOST')
    port = int(os.environ.get('FTP_PORT', 21))
    user = os.environ.get('FTP_USER')
    password = os.environ.get('FTP_PASS')
    remote_dir = os.environ.get('FTP_WATCH_DIR', '/')

    seen_files = load_state()

    print(f"[*] Connecting to FTP server: {host}")
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=30)
        ftp.login(user, password)
        ftp.cwd(remote_dir)
        
        current_files = ftp.nlst()
        ftp.quit()
    except Exception as e:
        print(f"[!] FTP Connection failed: {e}")
        return

    new_files = [f for f in current_files if f not in seen_files and f not in ('.', '..')]

    if not new_files:
        print("[*] No new files detected.")
    else:
        print(f"[+] Found {len(new_files)} new file(s):")
        notification_message = f"Found {len(new_files)} new file(s) in FTP:\n"
        
        for filename in new_files:
            print(f"  - {filename}")
            notification_message += f"- {filename}\n"
            seen_files.add(filename)

        save_state(seen_files)
        
        # שליחת ההתראה ל-Pushover
        send_pushover_notification(notification_message.strip())

if __name__ == "__main__":
    watch_ftp_folder()
