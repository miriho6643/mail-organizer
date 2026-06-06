# database.py

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("emails.db")


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            body TEXT,
            category TEXT,
            privacy_priority INTEGER,
            summary TEXT,
            ai_reply TEXT,
            date_received TEXT,
            has_attachment INTEGER DEFAULT 0,
            auto_replied INTEGER DEFAULT 0
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            report_text TEXT
        )
        """)

        self.conn.commit()

    def add_email(
        self,
        message_id,
        sender,
        recipient,
        subject,
        body,
        category="unknown",
        privacy_priority=10,
        summary="",
        ai_reply="",
        has_attachment=False
    ):
        cur = self.conn.cursor()

        try:
            cur.execute("""
            INSERT INTO emails (
                message_id,
                sender,
                recipient,
                subject,
                body,
                category,
                privacy_priority,
                summary,
                ai_reply,
                date_received,
                has_attachment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                sender,
                recipient,
                subject,
                body,
                category,
                privacy_priority,
                summary,
                ai_reply,
                datetime.now().isoformat(),
                int(has_attachment)
            ))

            self.conn.commit()

        except sqlite3.IntegrityError:
            pass

    def get_all_emails(self):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT *
        FROM emails
        ORDER BY date_received DESC
        """)

        return cur.fetchall()

    def search_emails(self, text):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT *
        FROM emails
        WHERE
            sender LIKE ?
            OR subject LIKE ?
            OR body LIKE ?
        ORDER BY date_received DESC
        """, (
            f"%{text}%",
            f"%{text}%",
            f"%{text}%"
        ))

        return cur.fetchall()

    def get_emails_by_priority(self, priority):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT *
        FROM emails
        WHERE privacy_priority = ?
        ORDER BY date_received DESC
        """, (priority,))

        return cur.fetchall()

    def mark_auto_replied(self, email_id):
        cur = self.conn.cursor()

        cur.execute("""
        UPDATE emails
        SET auto_replied = 1
        WHERE id = ?
        """, (email_id,))

        self.conn.commit()

    def save_setting(self, key, value):
        cur = self.conn.cursor()

        cur.execute("""
        INSERT OR REPLACE INTO settings
        (key, value)
        VALUES (?, ?)
        """, (key, value))

        self.conn.commit()

    def get_setting(self, key, default=None):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT value
        FROM settings
        WHERE key = ?
        """, (key,))

        row = cur.fetchone()

        if row:
            return row[0]

        return default

    def save_report(self, report_text):
        cur = self.conn.cursor()

        cur.execute("""
        INSERT INTO reports
        (created_at, report_text)
        VALUES (?, ?)
        """, (
            datetime.now().isoformat(),
            report_text
        ))

        self.conn.commit()

    def get_reports(self):
        cur = self.conn.cursor()

        cur.execute("""
        SELECT *
        FROM reports
        ORDER BY created_at DESC
        """)

        return cur.fetchall()

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db = Database()

    db.add_email(
        message_id="test123",
        sender="example@test.com",
        recipient="me@test.com",
        subject="Testmail",
        body="Hallo Welt"
    )

    print(db.get_all_emails())

