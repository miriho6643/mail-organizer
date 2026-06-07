# config.py

import json
from pathlib import Path

DEFAULT_CONFIG = {
    "openrouter_key": "YOUR_KEY_HERE",
    "report_email": "max.mustermann@gmail.com",
    "dark_mode": False,
    "interval": 300,

    "accounts": [
        {
            "name": "gmail",
            "email": "max.mustermann@gmail.com",
            "password": "PASSWORD",
            "imap": "imap.gmail.com",
            "smtp": "smtp.gmail.com"
        },
        {
            "name": "outlook",
            "email": "max.mustermann@outlook.com",
            "password": "PASSWORD",
            "imap": "outlook.office365.com",
            "smtp": "smtp.office365.com"
        }
    ]
}


class Config:

    def __init__(self, path="config.json"):
        self.path = Path(path)
        self.data = self.load()

    def load(self):

        if not self.path.exists():
            self.create_default()

        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_default(self):

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)

        print("[CONFIG] Default config.json erstellt")

    def save(self):

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):

        self.data[key] = value
        self.save()

if __name__ == "__main__":
    config = Config()
    print(config.data)