from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame, QHBoxLayout, QLineEdit, QLabel, QCheckBox, QGridLayout, QComboBox, QFileDialog, QProgressBar
from PyQt6.QtCore import Qt, QTimer
import sys
import os
import json
import yt_dlp
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv
from utils.trimmer import trim_args

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
SETTINGS_FILE = "settings.json"

theme_styles = {
    "light": "",
    "dark": """
        QWidget {
            background-color: #1E1E1E; /* Dark Gray */
            color: #D0D0D0; /* Light Gray */
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
            box-shadow: 2px 2px 6px #000;
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
        QProgressBar {
            border: 2px solid #555;
            border-radius: 5px;
            background-color: #2A2A2A;
        }
        QProgressBar::chunk {
            background-color: #0078D7;
            width: 20px;
        }
    """
}

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
    
    def load_last_selected_folder(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as file:
                    settings = json.load(file)
                    return settings.get("last_selected_folder", os.path.expanduser("~/Downloads"))
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return os.path.expanduser("~/Downloads")
    
    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.setStyleSheet(theme_styles[self.current_theme])
        self.card.setStyleSheet(theme_styles[self.current_theme])

class Card(QFrame):
    def __init__(self, parent=None, default_folder=""):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        self.is_downloading = False
        layout = QVBoxLayout(self)
        
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
        
        self.switch = QCheckBox("Partial")
        self.switch.stateChanged.connect(self.toggle_partial_fields)
        
        self.from_input = QLineEdit()
        self.from_input.setPlaceholderText("From (hh:mm:ss)")
        self.from_input.setVisible(False)
        
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("To (hh:mm:ss)")
        self.to_input.setVisible(False)
        
        self.quality_selector = QComboBox()
        self.quality_selector.addItems(["1080p", "720p", "480p", "360p", "240p", "144p"])
        
        self.download_button = QPushButton("Download")
        self.download_button.setVisible(False)
        self.download_button.clicked.connect(self.start_download)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        layout.addLayout(top_layout)
        layout.addWidget(self.quality_selector)
        layout.addWidget(self.switch)
        layout.addWidget(self.from_input)
        layout.addWidget(self.to_input)
        layout.addWidget(self.download_button)
        layout.addWidget(self.progress_bar)
        
        self.url_input.textChanged.connect(self.update_download_button)
        self.switch.stateChanged.connect(self.update_download_button)
        
    def open_folder_dialog(self):
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_input.setText(folder_path)
    
    def toggle_partial_fields(self):
        checked = self.switch.isChecked()
        self.from_input.setVisible(checked)
        self.to_input.setVisible(checked)
        self.update_download_button()
    
    def update_download_button(self):
        url_valid = bool(self.url_input.text().strip())
        folder_valid = bool(self.folder_input.text().strip())
        self.download_button.setVisible(url_valid and folder_valid)
    
    def start_download(self):
        if self.is_downloading:
            return
        self.is_downloading = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        opts = {
            "outtmpl": os.path.join(self.folder_input.text(), "input"),
            "external_downloader": ffmpeg_path,
            "format": "bestvideo[height<=" + self.quality_selector.currentText()[:-1] + "]+bestaudio/best",
        }
        url = self.url_input.text().strip()
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(url)
        self.is_downloading = False
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouT