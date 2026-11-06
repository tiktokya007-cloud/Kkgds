import os
import json
import time
import ftplib
from pathlib import Path

STATE_FILE = ".watcher_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_state(seen_files):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen_files), f)

def run_watcher_once():
    # Load configuration from environment variables (injected by GitHub Actions)
    host = os.environ.get("FTP_HOST")
    port = int(os.environ.get("FTP_PORT", 21))
    user = os.environ.get("FTP_USER")
    password = os.environ.get("FTP_PASS")
    remote_dir = os.environ.get("FTP_WATCH_DIR", "/")
    
    # In GitHub Actions, we can download files to a temporary or workspace folder
    secret_dir = Path("./downloaded_files")
    secret_dir.mkdir(parents=True, exist_ok=True)

    seen_files = load_state()

    print(f"[*] Connecting to FTP server: {host}")
    
    ftp = ftplib.FTP()
    ftp.connect(host, port, timeout=30)
    ftp.login(user, password)
    ftp.cwd(remote_dir)

    current_files = ftp.nlst()
    new_files = [f for f in current_files if f not in seen_files and f not in ('.', '..')]

    if not new_files:
        print("[*] No new files found.")
    else:
        for filename in new_files:
            local_file_path = secret_dir / filename
            print(f"[+] New file detected: {filename}. Downloading...")

            with open(local_file_path, "wb") as local_file:
                ftp.retrbinary(f"RETR {filename}", local_file.write)

            print(f"[✓] Successfully downloaded: {filename}")
            
            seen_files.add(filename)
            save_state(seen_files)

    ftp.quit()

if __name__ == "__main__":
    run_watcher_once()
