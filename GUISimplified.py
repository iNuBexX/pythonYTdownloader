from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame,
    QHBoxLayout, QLineEdit, QLabel, QCheckBox, QGridLayout, QComboBox, QFileDialog,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import os
import json
import yt_dlp
import traceback
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv
import re
from utils.trimmer import trim_args
from utils.conversion import Converter  
from utils.formatparser import get_format_option

vidConverter = Converter()
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
SETTINGS_FILE = "settings.json"

theme_styles = {
    "light": "",
    "dark": """
        QWidget {
            background-color: #1E1E1E;
            color: #D0D0D0;
            font-size: 14px;
        }
        QPushButton {
            background-color: #2D2D2D;
            border: 2px solid #555;
            border-radius: 6px;
            color: #D0D0D0;
            padding: 8px;
        }
        QPushButton:hover {
            background-color: #3C3C3C;
            border: 2px solid #777;
        }
        QLineEdit {
            background-color: #252525;
            border: 2px solid #555;
            border-radius: 4px;
            padding: 6px;
            color: #D0D0D0;
        }
        QFrame {
            background-color: #252525;
            border: 2px solid #444;
            border-radius: 10px;
            padding: 12px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #D0D0D0;
            background-color: #2A2A2A;
            border-radius: 4px;
        }
        QCheckBox::indicator:checked {
            background-color: #0078D7;
            border: 2px solid #0078D7;
        }

    """
}


def dump_all_files(error_message, folder, ui_state=""):
    error_log = "error.txt"
    try:
        with open(error_log, "w", encoding="utf-8") as f:
            f.write("Error occurred:\n")
            f.write(error_message + "\n\n")
            f.write("UI State:\n" + ui_state + "\n\n")
            f.write("Dumping files in folder: " + folder + "\n")
            for file in os.listdir(folder):
                f.write(file + "\n")
    except Exception as e:
        print("Failed to dump error info:", e)


# Worker thread for downloading
class DownloadThread(QThread):
    download_finished = pyqtSignal()
    
    def __init__(self, url, opts, ui_state="", parent=None):
        super().__init__(parent)
        self.url = url
        self.opts = opts
        self.ui_state = ui_state
        
    def run(self):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                ydl.download([self.url])
        except Exception as e:
            dump_all_files(traceback.format_exc(), ".", self.ui_state)
        self.download_finished.emit()

# Worker thread for conversion
class ConversionThread(QThread):
    conversion_finished = pyqtSignal()
    
    def __init__(self, input_base, output_filedir, output_fileName, deletesOriginal, ui_state="", parent=None):
        super().__init__(parent)
        self.input_base = input_base
        self.output_filedir = output_filedir
        self.output_fileName = output_fileName
        self.deletesOriginal = deletesOriginal
        self.ui_state = ui_state
        
    def run(self):
        try:
            vidConverter.convert_webm_to_mp4(self.input_base, self.output_filedir, self.output_fileName, self.deletesOriginal)
        except Exception as e:
            dump_all_files(traceback.format_exc(), ".", self.ui_state)
        self.conversion_finished.emit()

class YouTubeTrimmer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GQIA YouTube Trimmer Tool")
        self.setGeometry(100, 100, 420, 250)
        
        self.last_selected_folder = self.load_last_selected_folder()
        self.current_theme = "dark"  # Default to dark theme
        self.setStyleSheet(theme_styles[self.current_theme])
        
        self.layout = QVBoxLayout(self)
        
        self.card = Card(self, self.last_selected_folder)
        self.card.setStyleSheet(theme_styles[self.current_theme])
        self.layout.addWidget(self.card)
        
        self.theme_switcher = QPushButton("Toggle Theme")
        self.theme_switcher.clicked.connect(self.toggle_theme)
        self.layout.addWidget(self.theme_switcher)
        
        self.setLayout(self.layout)
        
        # Create an overlay widget to indicate downloading in progress
        self.download_overlay = QWidget(self)
        self.download_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
        self.download_overlay.setGeometry(0, 0, self.width(), self.height())
        overlay_layout = QVBoxLayout(self.download_overlay)
        overlay_layout.addStretch()
        self.downloading_label = QLabel("Downloading...", self.download_overlay)
        self.downloading_label.setStyleSheet("font-size: 20px; color: white;")
        self.downloading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self.downloading_label)
        overlay_layout.addStretch()
         # Add a cancel button to the overlay.
        self.cancel_button = QPushButton("Cancel", self.download_overlay)
        self.cancel_button.setStyleSheet("font-size: 16px; padding: 6px;")
        self.cancel_button.clicked.connect(self.cancel_current_download)
        overlay_layout.addWidget(self.cancel_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.download_overlay.hide()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.download_overlay.setGeometry(0, 0, self.width(), self.height())
    
    def load_last_selected_folder(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as file:
                    settings = json.load(file)
                    return settings.get("last_selected_folder", os.path.expanduser("~/Downloads"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return os.path.expanduser("~/Downloads")
    
    def save_last_selected_folder(self, folder):
        settings = {"last_selected_folder": folder}
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file)
    
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.setStyleSheet(theme_styles[self.current_theme])
        self.card.setStyleSheet(theme_styles[self.current_theme])

    def show_download_overlay(self, text="Downloading..."):
        self.downloading_label.setText(text)
        self.download_overlay.show()
    
    def hide_download_overlay(self):
        self.download_overlay.hide()
    
    def cancel_current_download(self):
        # Call the card's cancel method to terminate any running thread.
        self.card.cancel_download()
        self.hide_download_overlay()

class Card(QFrame):
    def __init__(self, parent=None, default_folder=""):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        self.is_downloading = False
        layout = QVBoxLayout(self)
        
        # Top row: URL and folder selection
        top_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link here...")
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Selected folder...")
        self.folder_input.setReadOnly(True)
        self.folder_input.setText(default_folder)
        
        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.open_folder_dialog)
        
        top_layout.addWidget(self.url_input)
        top_layout.addWidget(self.folder_input)
        top_layout.addWidget(self.folder_button)
        
        # Additional fields: quality and download name
        self.quality_selector = QComboBox()
        self.quality_selector.addItems(["1080p", "720p", "480p", "360p", "240p", "144p", "audio-only"])
        
        self.download_name_input = QLineEdit()
        self.download_name_input.setPlaceholderText("Download under name:")
        
        # Partial download option with from/to fields
        self.switch = QCheckBox("Partial")
        self.switch.stateChanged.connect(self.toggle_partial_fields)
        
        self.from_input = QLineEdit()
        self.from_input.setPlaceholderText("From (hh:mm:ss)")
        self.from_input.setVisible(False)
        
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("To (hh:mm:ss)")
        self.to_input.setVisible(False)
        
        self.download_button = QPushButton("Download")
        self.download_button.setVisible(False)
        self.download_button.clicked.connect(self.start_download)
        
        
        # Add widgets to layout
        layout.addLayout(top_layout)
        layout.addWidget(self.quality_selector)
        layout.addWidget(self.download_name_input)
        layout.addWidget(self.switch)
        layout.addWidget(self.from_input)
        layout.addWidget(self.to_input)
        layout.addWidget(self.download_button)
        
        # Connect changes to update button visibility
        self.url_input.textChanged.connect(self.update_download_button)
        self.switch.stateChanged.connect(self.update_download_button)
        self.from_input.textChanged.connect(self.update_download_button)
        self.to_input.textChanged.connect(self.update_download_button)
        self.download_name_input.textChanged.connect(self.update_download_button)
    
    def open_folder_dialog(self):
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_input.setText(folder_path)
            # Update the main window's last folder and save it
            self.parent().last_selected_folder = folder_path
            self.parent().save_last_selected_folder(folder_path)
    
    def toggle_partial_fields(self):
        checked = self.switch.isChecked()
        self.from_input.setVisible(checked)
        self.to_input.setVisible(checked)
        self.update_download_button()
    
    def is_valid_time_format(self, time_str):
        """Check if time_str is in hh:mm:ss or mm:ss format."""
        return bool(re.fullmatch(r'(\d{1,2}:)?\d{1,2}:\d{2}', time_str))
    
    def convert_to_seconds(self, time_str):
        """Convert hh:mm:ss or mm:ss to total seconds for comparison."""
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return 0
    
    def get_ui_state(self):
        """Return a string with the current UI field values."""
        state = []
        state.append("URL: " + self.url_input.text())
        state.append("Folder: " + self.folder_input.text())
        state.append("Download Name: " + self.download_name_input.text())
        state.append("Quality: " + self.quality_selector.currentText())
        state.append("Partial: " + str(self.switch.isChecked()))
        if self.switch.isChecked():
            state.append("From: " + self.from_input.text())
            state.append("To: " + self.to_input.text())
        return "\n".join(state)
    
    def update_download_button(self):
        url_valid = bool(self.url_input.text().strip())
        folder_valid = bool(self.folder_input.text().strip())
        download_name_valid = bool(self.download_name_input.text().strip())
        if self.switch.isChecked():
            from_text = self.from_input.text().strip()
            to_text = self.to_input.text().strip()
            from_valid = self.is_valid_time_format(from_text)
            to_valid = self.is_valid_time_format(to_text)
            # Ensure "To" is after "From"
            time_valid = from_valid and to_valid and self.convert_to_seconds(to_text) > self.convert_to_seconds(from_text)
            self.download_button.setVisible(url_valid and folder_valid and download_name_valid and time_valid)
        else:
            self.download_button.setVisible(url_valid and folder_valid and download_name_valid)
    
    def start_download(self):
        if self.is_downloading:
            return
        self.is_downloading = True

        if self.switch.isChecked():
            ffmpeg_args = trim_args(self.from_input.text(), self.to_input.text())
        else:
            ffmpeg_args = {}
        # Use the download name from the input field (default to "input" if empty)
        download_name = self.download_name_input.text().strip() or "input"
        if self.quality_selector.currentText() == "audio-only":
            # Ensure the output name ends with .wav for audio-only downloads
            out_name = download_name if download_name.endswith(".wav") else download_name + ".wav"
        else:
            out_name = download_name
        opts = {
            "outtmpl": os.path.join(self.folder_input.text(), out_name),
            "external_downloader": ffmpeg_path,
            "external_downloader_args": ffmpeg_args,
            "format":  get_format_option(self.quality_selector.currentText()),
        }
        url = self.url_input.text().strip()
        
        ui_state = self.get_ui_state()
        # Show the overlay from the parent (main window)
        self.parent().show_download_overlay()
        
        # Create and start the download thread
        self.download_thread = DownloadThread(url, opts,ui_state, parent=self)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_finished(self):
        download_name = self.download_name_input.text().strip() or "input"
        # If the download name already ends with .mp3 or .wav, skip conversion.
        if self.quality_selector.currentText() == "audio-only":
            self.parent().hide_download_overlay()
            self.is_downloading = False
            return
        self.parent().show_download_overlay("Converting...")
        input_base = os.path.join(self.folder_input.text(), download_name)
        output_fileName = download_name if download_name.endswith(".mp4") else download_name + ".mp4"
        # Create and start the conversion thread.
        self.conversion_thread = ConversionThread(input_base, self.folder_input.text(), output_fileName, deletesOriginal=True)
        self.conversion_thread.conversion_finished.connect(self.on_conversion_finished)
        self.conversion_thread.start()

    def on_conversion_finished(self):
        self.is_downloading = False
        # Hide the overlay and reset overlay text
        self.parent().hide_download_overlay()
        self.parent().downloading_label.setText("Downloading...")

    def cancel_download(self):
        # If a download thread is running, terminate it.
        if self.download_thread is not None and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
            self.download_thread = None
        # Also cancel conversion thread if running.
        if hasattr(self, "conversion_thread") and self.conversion_thread is not None and self.conversion_thread.isRunning():
            self.conversion_thread.terminate()
            self.conversion_thread.wait()
            self.conversion_thread = None
        self.is_downloading = False
        self.parent().hide_download_overlay()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeTrimmer()
    window.show()
    sys.exit(app.exec())
