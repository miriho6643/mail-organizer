# worker.py

import time
import json
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal
from pytest import Config

from mail_client import MailClient
from ai import AIClient
from database import Database
from config import Config


BLOCKED_WORDS = [
    "rechnung",
    "vertrag",
    "kündigung",
    "passwort",
    "bank",
    "zahlung",
    "ausweis",
    "identität"
]


class MailWorker(QObject):

    log_message = pyqtSignal(str)
    emails_updated = pyqtSignal()

    def __init__(self, config_path="config.json"):
        super().__init__()

        self.running = False

        self.db = Database()

        self.config_path = config_path
        self.config = Config().data

        self.interval = self.config.get("interval", 300)

        self.ai = AIClient(self.config["openrouter_key"])

        self.clients = self.init_clients()

    # --------------------------
    # CONFIG
    # --------------------------

    def load_config(self):

        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # --------------------------
    # INIT MAIL ACCOUNTS
    # --------------------------

    def init_clients(self):

        clients = []

        for acc in self.config["accounts"]:

            clients.append(
                MailClient(acc)
            )

        return clients

    # --------------------------
    # LOGGING
    # --------------------------

    def log(self, text):

        msg = f"[{datetime.now()}] {text}"

        print(msg)

        try:
            self.log_message.emit(msg)
        except:
            pass

    # --------------------------
    # SECURITY CHECK
    # --------------------------

    def is_sensitive(self, subject, body):

        text = (subject + " " + body).lower()

        return any(word in text for word in BLOCKED_WORDS)

    # --------------------------
    # PROCESS EMAIL
    # --------------------------

    def process_email(self, mail_data):

        sender = mail_data["sender"]
        subject = mail_data["subject"]
        body = mail_data["body"]
        message_id = mail_data["message_id"]
        has_attachment = mail_data["has_attachment"]
        account = mail_data["account"]

        self.log(f"Analysiere ({account}): {subject}")

        analysis = self.ai.analyze_email(
            sender,
            subject,
            body
        )

        priority = int(analysis.get("privacy_priority", 10))
        category = analysis.get("category", "unknown")
        summary = analysis.get("summary", "")
        reply = analysis.get("suggested_reply", "")

        self.db.add_email(
            message_id=message_id,
            sender=sender,
            recipient=account,
            subject=subject,
            body=body,
            category=category,
            privacy_priority=priority,
            summary=summary,
            ai_reply=reply,
            has_attachment=has_attachment
        )

        # --------------------------
        # RULE ENGINE
        # --------------------------

        if has_attachment or self.is_sensitive(subject, body):
            self.log("Blockiert (sensibel)")
            return

        if priority >= 8:
            self.log("Privat → kein Auto-Reply")
            return

        if priority >= 6:
            self.log("Antwort gespeichert (kein Send)")
            return

        if priority >= 3:

            self.log("Auto-Reply wird gesendet")

            try:
                client = self.get_client_by_account(account)

                client.send_email(
                    recipient=sender,
                    subject=f"Re: {subject}",
                    body=reply
                )

                self.log("Antwort gesendet")

                self.db.mark_auto_replied(message_id)

            except Exception as e:
                self.log(f"SMTP Fehler: {e}")

        elif priority == 2:
            self.log("Werbung → archiviert")

        else:
            self.log("Spam ignoriert")

    # --------------------------
    # GET CLIENT
    # --------------------------

    def get_client_by_account(self, account_name):

        for c in self.clients:
            if c.name == account_name:
                return c

        return self.clients[0]

    # --------------------------
    # RUN ONCE
    # --------------------------

    def run_once(self):

        try:

            total = 0

            for client in self.clients:

                emails = client.get_unseen_emails()

                self.log(
                    f"{client.name}: {len(emails)} neue Mails"
                )

                for mail in emails:
                    self.process_email(mail)
                    total += 1

            self.log(f"Insgesamt verarbeitet: {total}")

            self.emails_updated.emit()

        except Exception as e:
            self.log(f"Worker Error: {e}")

    # --------------------------
    # LOOP
    # --------------------------

    def run(self):

        self.running = True

        self.log("Worker gestartet")

        while self.running:

            self.run_once()

            for _ in range(
                int(self.config.get("interval", 300))
            ):
                if not self.running:
                    break
                time.sleep(1)

        self.log("Worker gestoppt")

    def stop(self):
        self.running = False
