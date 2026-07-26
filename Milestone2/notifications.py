"""
FranchiseOps AI - notifications.py
Multi-channel alert center simulating SMS, Email, and In-App notifications stored in SQLite.
"""
from db import get_conn

def send_alert(channel, recipient, subject, message):
    with get_conn() as conn:
        conn.execute("INSERT INTO notifications (channel, recipient, subject, message, status) VALUES (?, ?, ?, ?, ?)",
                     (channel, recipient, subject, message, "Delivered"))
        conn.commit()
    print(f"[{channel.upper()}] To: {recipient} | Subject: {subject} | Status: Delivered")

def get_recent_alerts(limit=15):
    with get_conn() as conn:
        return conn.execute("SELECT id, channel, recipient, subject, message, created_at FROM notifications ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
