import os
import time
import csv
import math
import shutil
import random
import threading
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QUrl, QMetaObject, Q_ARG
from PySide6.QtGui import QDesktopServices, QFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

TMP_DIR = "tmp"
DONE_DIR = "done"
BATCH_SIZE = 500
BATCH_PAUSE = 60
DELAY_MIN = 2
DELAY_MAX = 5

tracking_file_path = ""

class RoyalMailApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Royal Mail Tracker")
        self.setFixedSize(500, 280)

        layout = QVBoxLayout()

        self.label = QLabel("")
        self.label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.label)

        self.btn_browse = QPushButton("Select Tracker File")
        self.btn_browse.clicked.connect(self.select_file)
        layout.addWidget(self.btn_browse)

        self.btn_start = QPushButton("Start Tracking")
        self.btn_start.clicked.connect(self.run_tracking_thread)
        layout.addWidget(self.btn_start)

        self.status_label = QLabel("")
        self.status_label.setTextFormat(Qt.RichText)
        self.status_label.setOpenExternalLinks(True)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.link_label = QLabel("Waiting...")
        self.link_label.setOpenExternalLinks(True)
        layout.addWidget(self.link_label)

        from PySide6.QtWidgets import QCheckBox

        self.checkbox_open = QCheckBox("Open file when done")
        self.checkbox_open.setChecked(False)
        help_button = QPushButton("?")
        help_button.setFixedWidth(25)
        help_button.setToolTip("Click to see how this program works")
        help_button.clicked.connect(self.show_help)

        from PySide6.QtWidgets import QHBoxLayout
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(20)
        bottom_layout.addWidget(help_button, alignment=Qt.AlignLeft)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.checkbox_open, alignment=Qt.AlignRight)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)
    

    def select_file(self):
        global tracking_file_path
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Tracker File", "", "Text Files (*.txt)")
        if file_path:
            tracking_file_path = file_path
            self.label.setText(f"Selected: {os.path.basename(file_path)}")

    def run_tracking_thread(self):
        if not tracking_file_path:
            QMessageBox.warning(self, "No file", "Please select a tracking file first.")
            return
        threading.Thread(target=self.start_tracking, daemon=True).start()

    def safe_update_status(self, text):
        QMetaObject.invokeMethod(self.status_label, "setText", Qt.QueuedConnection, Q_ARG(str, text))

    def safe_update_progress(self, value):
        QMetaObject.invokeMethod(self.progress, "setValue", Qt.QueuedConnection, Q_ARG(int, value))

    def safe_update_link(self, html):
        QMetaObject.invokeMethod(self.link_label, "setText", Qt.QueuedConnection, Q_ARG(str, html))

    def show_help(self):
        QMessageBox.information(
           self,
           "How it works",
           "This tool splits the original list of tracking codes into batches of up to 500 codes.\n\n"
           "For each batch, it opens a new browser window, processes the codes, and then closes the browser.\n\n"
           "This helps simulate more human-like behavior and avoid detection when using automation.\n\n"
           "A .csv file will be generated in the 'done' folder with the results."
       )

    def open_file(self, path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def start_tracking(self):
        self.checkbox_open.setDisabled(True)
        os.makedirs(TMP_DIR, exist_ok=True)
        os.makedirs(DONE_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        csv_filename = f"results_{timestamp}.csv"
        csv_path = os.path.abspath(os.path.join(DONE_DIR, csv_filename))

        with open(tracking_file_path, "r") as f:
            tracking_codes = [line.strip() for line in f if line.strip()]

        total_codes = len(tracking_codes)
        processed = 0

        num_batches = math.ceil(total_codes / BATCH_SIZE)
        for i in range(num_batches):
            batch = tracking_codes[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
            with open(f"{TMP_DIR}/batch_{i+1}.txt", "w") as f:
                f.write("\n".join(batch))

        with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow(["Tracking Code", "Status", "Message"])

            for batch_index in range(num_batches):
                batch_path = f"{TMP_DIR}/batch_{batch_index+1}.txt"
                current_batch_total = len(open(batch_path).readlines())
                current_batch_progress = 0
                self.safe_update_status(f"Processing batch {batch_index+1}/{num_batches}...")

                options = webdriver.ChromeOptions()
                options.add_argument("--start-maximized")
                options.add_argument("--disable-blink-features=AutomationControlled")
                driver = webdriver.Chrome(options=options)

                stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                )

                with open(batch_path, "r") as f:
                    codes = [line.strip() for line in f if line.strip()]

                for code in codes:
                    try:
                        driver.get("https://www.royalmail.com/track-your-item")
                        time.sleep(3)
                        try:
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.ID, "consent_prompt_submit"))
                            ).click()
                        except:
                            pass

                        self.safe_update_status("🍪 Cookie accepted. Scanning...")

                        input_box = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "barcode-input"))
                        )
                        input_box.clear()
                        input_box.send_keys(code)

                        track_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
                        )
                        track_button.click()

                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".track-item-status, #errorMessage"))
                        )

                        try:
                            error_elem = driver.find_element(By.ID, "errorMessage")
                            message = error_elem.text.strip()
                            status = "Not found"
                        except:
                            status_elem = driver.find_element(By.CSS_SELECTOR, ".track-item-status")
                            message = status_elem.text.strip()
                            status = "Delivered" if "delivered" in message.lower() else "In transit"

                        writer.writerow([code, status, message])
                        processed += 1
                        current_batch_progress += 1
                        percent = int((processed / total_codes) * 100)
                        progress_text = f"📦 Batch {batch_index+1} – {current_batch_progress}/{current_batch_total} ({percent}%)"
                        self.safe_update_progress(percent)
                        self.safe_update_link(progress_text)
                        self.safe_update_status(f"{code}: {status}")
                    except Exception as e:
                        writer.writerow([code, "Error", str(e)])
                        processed += 1
                        current_batch_progress += 1
                        percent = int((processed / total_codes) * 100)
                        progress_text = f"📦 Batch {batch_index+1} – {current_batch_progress}/{current_batch_total} ({percent}%)"
                        self.safe_update_progress(percent)
                        self.safe_update_link(progress_text)
                        self.safe_update_status(f"{code}: Error")
                    time.sleep(random.randint(DELAY_MIN, DELAY_MAX))

                if percent < 100:
                  time.sleep(BATCH_PAUSE)
                else:
                  self.safe_update_status("⏳ Please wait, finalizing file...")

                driver.quit()

        shutil.rmtree(TMP_DIR)
        time.sleep(0.5)
        self.safe_update_status(f'<a href="file://{csv_path}">✅ Done. Results saved to {os.path.basename(csv_path)}</a>')
        self.safe_update_progress(100)
        self.safe_update_link("Done...")
        self.checkbox_open.setDisabled(False)
        if self.checkbox_open.isChecked():
            self.open_file(csv_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RoyalMailApp()
    window.show()
    sys.exit(app.exec())
