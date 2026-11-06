import os
import json
import ftplib

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

def watch_ftp_folder():
    host = os.environ.get("FTP_HOST")
    port = int(os.environ.get("FTP_PORT", 21))
    user = os.environ.get("FTP_USER")
    password = os.environ.get("FTP_PASS")
    remote_dir = os.environ.get("FTP_WATCH_DIR", "/")

    seen_files = load_state()

    print(f"[*] Connecting to FTP server: {host}")
    
    ftp = ftplib.FTP()
    ftp.connect(host, port, timeout=30)
    ftp.login(user, password)
    ftp.cwd(remote_dir)

    current_files = ftp.nlst()
    
    new_files = [f for f in current_files if f not in seen_files and f not in ('.', '..')]

    if not new_files:
        print("[*] No new files detected.")
    else:
        print(f"[+] Found {len(new_files)} new file(s):")
        for filename in new_files:
            print(f"    - {filename}")
            seen_files.add(filename)

        save_state(seen_files)

    ftp.quit()

if __name__ == "__main__":
    watch_ftp_folder()
