# main.py

import sys
import threading

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QMessageBox,
    QCheckBox
)

from database import Database
from worker import MailWorker
from config import Config


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Mail Assistant")
        self.resize(1200, 700)

        self.db = Database()
        self.config = Config()

        self.worker = None
        self.worker_thread = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.create_dashboard()
        self.create_inbox()
        self.create_logs()
        self.create_settings()

    # -------------------------
    # DASHBOARD
    # -------------------------

    def create_dashboard(self):

        tab = QWidget()
        layout = QVBoxLayout()

        self.status_label = QLabel("Status: Stopped")

        start_btn = QPushButton("Worker starten")
        stop_btn = QPushButton("Worker stoppen")

        start_btn.clicked.connect(self.start_worker)
        stop_btn.clicked.connect(self.stop_worker)

        layout.addWidget(self.status_label)
        layout.addWidget(start_btn)
        layout.addWidget(stop_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Dashboard")

    # -------------------------
    # INBOX
    # -------------------------

    def create_inbox(self):

        tab = QWidget()
        layout = QVBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Suche E-Mails...")

        search_btn = QPushButton("Suchen")
        search_btn.clicked.connect(self.search_emails)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Sender",
            "Betreff",
            "Kategorie",
            "Priorität",
            "Zusammenfassung"
        ])

        load_btn = QPushButton("Laden")
        load_btn.clicked.connect(self.load_emails)

        top = QHBoxLayout()
        top.addWidget(self.search)
        top.addWidget(search_btn)

        layout.addLayout(top)
        layout.addWidget(self.table)
        layout.addWidget(load_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Inbox")

    # -------------------------
    # LOGS
    # -------------------------

    def create_logs(self):

        tab = QWidget()
        layout = QVBoxLayout()

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addWidget(self.log_box)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Logs")

    # -------------------------
    # SETTINGS
    # -------------------------

    def create_settings(self):

        tab = QWidget()
        layout = QVBoxLayout()

        self.dark_mode = QCheckBox("Dark Mode")
        self.dark_mode.setChecked(self.config.get("dark_mode", False))
        self.dark_mode.stateChanged.connect(self.toggle_dark_mode)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("OpenRouter API Key")

        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.save_settings)

        layout.addWidget(QLabel("Einstellungen"))
        layout.addWidget(self.dark_mode)
        layout.addWidget(self.api_input)
        layout.addWidget(save_btn)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Settings")

    # -------------------------
    # WORKER CONTROL
    # -------------------------

    def start_worker(self):

        if self.worker:
            return

        self.status_label.setText("Status: Running")

        self.worker = MailWorker()

        self.worker_thread = threading.Thread(
            target=self.worker.run,
            daemon=True
        )

        self.worker.log_message.connect(self.add_log)
        self.worker.emails_updated.connect(self.load_emails)

        self.worker_thread.start()

    def stop_worker(self):

        if self.worker:
            self.worker.stop()
            self.worker = None

        self.status_label.setText("Status: Stopped")

    # -------------------------
    # LOGGING
    # -------------------------

    def add_log(self, text):
        self.log_box.append(text)

    # -------------------------
    # EMAILS
    # -------------------------

    def load_emails(self):

        emails = self.db.get_all_emails()

        self.table.setRowCount(len(emails))

        for r, e in enumerate(emails):

            self.table.setItem(r, 0, QTableWidgetItem(str(e[2])))
            self.table.setItem(r, 1, QTableWidgetItem(str(e[4])))
            self.table.setItem(r, 2, QTableWidgetItem(str(e[6])))
            self.table.setItem(r, 3, QTableWidgetItem(str(e[7])))
            self.table.setItem(r, 4, QTableWidgetItem(str(e[8])))

    def search_emails(self):

        q = self.search.text()
        results = self.db.search_emails(q)

        self.table.setRowCount(len(results))

        for r, e in enumerate(results):

            self.table.setItem(r, 0, QTableWidgetItem(str(e[2])))
            self.table.setItem(r, 1, QTableWidgetItem(str(e[4])))
            self.table.setItem(r, 2, QTableWidgetItem(str(e[6])))
            self.table.setItem(r, 3, QTableWidgetItem(str(e[7])))
            self.table.setItem(r, 4, QTableWidgetItem(str(e[8])))

    # -------------------------
    # SETTINGS HANDLING
    # -------------------------

    def save_settings(self):

        key = self.api_input.text().strip()

        if key:
            self.config.set("openrouter_key", key)

        self.config.set(
            "dark_mode",
            self.dark_mode.isChecked()
        )

        QMessageBox.information(
            self,
            "OK",
            "Gespeichert"
        )

    # -------------------------
    # DARK MODE (simple)
    # -------------------------

    def toggle_dark_mode(self):

        if self.dark_mode.isChecked():
            self.setStyleSheet("background-color: #ffffff; color: black;")
        else:
            self.setStyleSheet("")


# -------------------------
# START
# -------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())