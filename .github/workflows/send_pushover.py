import os
import urllib.parse
import urllib.request


def send_pushover_notification():
    user_key = os.environ.get("PUSHOVER_USER_KEY")
    app_token = os.environ.get("PUSHOVER_APP_TOKEN")
    actor = os.environ.get("GITHUB_ACTOR", "Someone")
    workflow_name = os.environ.get("GITHUB_WORKFLOW", "Workflow")

    if not user_key or not app_token:
        print("Error: Pushover credentials not found in environment variables.")
        exit(1)

    message = f"🚀 Workflow '{workflow_name}' was manually triggered by @{actor}!"

    data = urllib.parse.urlencode(
        {
            "token": app_token,
            "user": user_key,
            "message": message,
            "title": "GitHub Actions Alert",
            "priority": 0,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.pushover.net/1/messages.json", data=data, method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("Pushover notification sent successfully!")
            else:
                print(f"Failed to send notification: Status {response.status}")
    except Exception as e:
        print(f"Error sending Pushover request: {e}")
        exit(1)


if __name__ == "__main__":
    send_pushover_notification()
