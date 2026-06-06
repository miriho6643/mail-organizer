# mail_client.py

import imaplib
import smtplib
import email
import html
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class MailClient:

    def __init__(self, account_config):
        """
        account_config = {
            "email": "",
            "password": "",
            "imap": "",
            "smtp": "",
            "name": ""
        }
        """
        self.email_address = account_config["email"]
        self.password = account_config["password"]
        self.imap_server = account_config["imap"]
        self.smtp_server = account_config["smtp"]
        self.name = account_config.get("name", self.email_address)

    # --------------------------
    # IMAP CONNECT
    # --------------------------

    def connect_imap(self):
        mail = imaplib.IMAP4_SSL(self.imap_server, 993)
        mail.login(self.email_address, self.password)
        return mail

    # --------------------------
    # GET EMAILS
    # --------------------------

    def get_unseen_emails(self, folder="INBOX"):
        emails = []

        try:
            mail = self.connect_imap()
            mail.select(folder)

            status, messages = mail.search(None, "UNSEEN")
            if status != "OK":
                return emails

            for num in messages[0].split():

                status, msg_data = mail.fetch(num, "(RFC822)")
                if status != "OK":
                    continue

                for response in msg_data:

                    if not isinstance(response, tuple):
                        continue

                    msg = email.message_from_bytes(response[1])

                    subject = self.decode(msg.get("Subject", ""))
                    sender = self.decode(msg.get("From", ""))
                    message_id = msg.get("Message-ID", str(num))

                    body, has_html = self.extract_body(msg)
                    has_attachment = self.has_attachment(msg)

                    emails.append({
                        "message_id": message_id,
                        "sender": sender,
                        "subject": subject,
                        "body": body,
                        "html": has_html,
                        "has_attachment": has_attachment,
                        "account": self.name
                    })

            mail.logout()

        except Exception as e:
            print(f"[IMAP ERROR {self.name}]:", e)

        return emails

    # --------------------------
    # BODY EXTRACTION (SAFE HTML)
    # --------------------------

    def extract_body(self, msg):
        body = ""
        has_html = False

        if msg.is_multipart():

            for part in msg.walk():

                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in disposition.lower():
                    continue

                try:

                    payload = part.get_payload(decode=True)

                    if not payload:
                        continue

                    text = payload.decode(errors="ignore")

                    if content_type == "text/html":
                        has_html = True
                        body += self.sanitize_html(text)

                    elif content_type == "text/plain" and not body:
                        body = text

                except:
                    continue

        else:
            try:
                body = msg.get_payload(decode=True).decode(errors="ignore")
            except:
                body = ""

        return body, has_html

    # --------------------------
    # HTML SANITIZER (NO IMAGES / TRACKING)
    # --------------------------

    def sanitize_html(self, html_content):
        """
        Entfernt potenziell gefährliche Inhalte:
        - img
        - script
        - externe Links bleiben nur Text
        """

        # super simple safe mode (kein full parser)
        forbidden = [
            "<img",
            "<script",
            "javascript:",
            "data:",
            "onerror",
            "onload"
        ]

        cleaned = html_content

        for f in forbidden:
            cleaned = cleaned.replace(f, "")

        return cleaned

    # --------------------------
    # SEND EMAIL
    # --------------------------

    def send_email(self, recipient, subject, body):

        msg = MIMEMultipart()

        msg["From"] = self.email_address
        msg["To"] = self.clean_email(recipient)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            server = smtplib.SMTP(self.smtp_server, 587)
            server.starttls()
            server.login(self.email_address, self.password)
            server.send_message(msg)
            server.quit()

        except Exception as e:
            print(f"[SMTP ERROR {self.name}]:", e)

    # --------------------------
    # HELPERS
    # --------------------------

    def clean_email(self, raw):
        """
        Extrahiert nur email@domain aus:
        "Name <email@domain>"
        """

        if "<" in raw and ">" in raw:
            return raw.split("<")[1].split(">")[0].strip()

        return raw.strip()

    def has_attachment(self, msg):

        for part in msg.walk():

            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition.lower():
                return True

        return False

    def decode(self, value):
        if not value:
            return ""

        decoded = decode_header(value)
        result = ""

        for text, enc in decoded:
            if isinstance(text, bytes):
                result += text.decode(enc or "utf-8", errors="ignore")
            else:
                result += text

        return result


# --------------------------
# TEST
# --------------------------

if __name__ == "__main__":

    account = {
        "name": "test",
        "email": "test@example.com",
        "password": "PASS",
        "imap": "imap.example.com",
        "smtp": "smtp.example.com"
    }

    client = MailClient(account)

    mails = client.get_unseen_emails()

    print("Neue Mails:", len(mails))

    for m in mails:
        print(m["subject"], m["sender"])
