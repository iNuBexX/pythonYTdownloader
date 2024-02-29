from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame,
    QHBoxLayout, QLineEdit, QLabel, QCheckBox, QGridLayout, QComboBox, QFileDialog,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import os
import json
import yt_dlp
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv
import re
import traceback
from utils.trimmer import trim_args
from utils.conversion import Converter  
from utils.formatparser import get_format_option

# Global converter instance.
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

# Helper function to dump error information and list files from a folder.
def dump_all_files(error_message, folder):
    error_log = "error.txt"
    try:
        with open(error_log, "w", encoding="utf-8") as f:
            f.write("Error occurred:\n")
            f.write(error_message + "\n\n")
            f.write("Dumping files in folder: " + folder + "\n")
            for file in os.listdir(folder):
                f.write(file + "\n")
    except Exception as e:
        # If writing to error.txt fails, print to stderr.
        print("Failed to dump error info:", e)

# Worker thread for downloading
class DownloadThread(QThread):
    download_finished = pyqtSignal()
    
    def __init__(self, url, opts, parent=None):
        super().__init__(parent)
        self.url = url
        self.opts = opts
        
    def run(self):
        try:
            with yt_dlp.YoutubeDL(self.opts) as ydl:
                ydl.download([self.url])
        except Exception as e:
            # Dump error info using the directory from outtmpl.
            folder = os.path.dirname(self.opts.get("outtmpl", ""))
            dump_all_files(traceback.format_exc(), folder)
        self.download_finished.emit()

# Worker thread for conversion
class ConversionThread(QThread):
    conversion_finished = pyqtSignal()
    
    def __init__(self, input_base, output_filedir, output_fileName, deletesOriginal, parent=None):
        super().__init__(parent)
        self.input_base = input_base
        self.output_filedir = output_filedir
        self.output_fileName = output_fileName
        self.deletesOriginal = deletesOriginal
        
    def run(self):
        try:
            vidConverter.convert_webm_to_mp4(self.input_base, self.output_filedir, self.output_fileName, self.deletesOriginal)
        except Exception as e:
            dump_all_files(traceback.format_exc(), self.output_filedir)
        self.conversion_finished.emit()

class YouTubeTrimmer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Trimmer Tool")
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
        
        # Create an overlay widget to indicate activity.
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
        self.download_thread = None
        self.conversion_thread = None
        layout = QVBoxLayout(self)
        
        # Top row: URL and folder selection.
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
        
        # Additional fields: quality and download name.
        self.quality_selector = QComboBox()
        self.quality_selector.addItems(["1080p", "720p", "480p", "360p", "240p", "144p", "audio-only"])
        
        self.download_name_input = QLineEdit()
        self.download_name_input.setPlaceholderText("Download under name:")
        
        # Partial download option with from/to fields.
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
        
        # Add widgets to layout.
        layout.addLayout(top_layout)
        layout.addWidget(self.quality_selector)
        layout.addWidget(self.download_name_input)
        layout.addWidget(self.switch)
        layout.addWidget(self.from_input)
        layout.addWidget(self.to_input)
        layout.addWidget(self.download_button)
        
        # Connect changes to update button visibility.
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
            # Update the main window's last folder and save it.
            self.parent().last_selected_folder = folder_path
            self.parent().save_
