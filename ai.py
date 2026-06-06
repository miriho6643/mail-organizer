# ai.py

import json
import requests


class AIClient:
    def __init__(self, api_key, model="deepseek/deepseek-chat-v3-0324:free"):
        self.api_key = api_key
        self.model = model

    def _ask(self, prompt):
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    def analyze_email(self, sender, subject, body):
        prompt = f"""
Analysiere diese E-Mail.

ABSENDER:
{sender}

BETREFF:
{subject}

INHALT:
{body}

Bewerte:

1. privacy_priority (1-10)

1 = Werbung / Spam / Routine
10 = sehr persönlich oder sensibel

2. category

Mögliche Werte:
- personal
- business
- support
- newsletter
- advertising
- spam

3. summary

Kurze Zusammenfassung in einem Satz.

4. suggested_reply

Eine passende Antwort.

Antworte AUSSCHLIESSLICH als JSON:

{{
  "privacy_priority": 1,
  "category": "",
  "summary": "",
  "suggested_reply": ""
}}
"""

        result = self._ask(prompt)

        try:
            return json.loads(result)

        except Exception:
            return {
                "privacy_priority": 10,
                "category": "unknown",
                "summary": "KI konnte die Nachricht nicht analysieren.",
                "suggested_reply": ""
            }

    def create_reply(self, sender, subject, body):
        prompt = f"""
Verfasse eine höfliche Antwort auf folgende E-Mail.

Absender:
{sender}

Betreff:
{subject}

Nachricht:
{body}

Antwort:
"""

        return self._ask(prompt)

    def summarize_month(self, email_data):
        prompt = f"""
Erstelle einen Monatsbericht aus folgenden E-Mails.

{email_data}

Der Bericht soll enthalten:

- Anzahl E-Mails
- Häufigste Kategorien
- Wichtigste Themen
- Kurze Zusammenfassung

Monatsbericht:
"""

        return self._ask(prompt)

    def chat(self, message):
        return self._ask(message)


if __name__ == "__main__":

    API_KEY = "DEIN_OPENROUTER_KEY"

    ai = AIClient(API_KEY)

    result = ai.analyze_email(
        sender="support@example.com",
        subject="Ticket Update",
        body="Ihr Ticket wurde erfolgreich bearbeitet."
    )

    print(json.dumps(result, indent=4, ensure_ascii=False))
