from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, 
    QFrame, QHBoxLayout, QLineEdit, QLabel, QCheckBox, QGridLayout, QComboBox, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QFileSystemWatcher, pyqtSignal, QThread
import sys
import os
import json
import re
import yt_dlp
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv
from utils.trimmer import trim_args
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
SETTINGS_FILE = "settings.json"
isDownloading = False
def is_valid_time_format(time_str):
    return re.match(r"^\d{2}:\d{2}:\d{2}$", time_str) is not None

class YouTubeTrimmer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Trimmer Tool")
        self.setGeometry(100, 100, 420, 550)
        
        self.last_selected_folder = self.load_last_selected_folder()

        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark", "Light"])
        self.theme_selector.currentIndexChanged.connect(self.change_theme)
        
        self.qss_watcher = QFileSystemWatcher(self)
        self.qss_watcher.fileChanged.connect(self.reload_stylesheet)
        
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.theme_selector)
        
        self.add_button = QPushButton("+ Add Video")
        self.add_button.setObjectName("addButton")
        self.add_button.clicked.connect(self.add_card)
        self.layout.addWidget(self.add_button)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)
        
        self.change_theme(0)
    
    def get_default_download_folder(self):
        if sys.platform == "win32":
            return os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            return os.path.join(os.path.expanduser("~"), "Downloads")
    
    def load_last_selected_folder(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as file:
                    settings = json.load(file)
                    return settings.get("last_selected_folder", self.get_default_download_folder())
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return self.get_default_download_folder()
    
    def save_last_selected_folder(self):
        with open(SETTINGS_FILE, "w") as file:
            json.dump({"last_selected_folder": self.last_selected_folder}, file)
    
    def add_card(self):
        card = Card(self, self.last_selected_folder)
        card.parentTrimmer = self
        self.scroll_layout.addWidget(card)
    
    def load_stylesheet(self, filename):
        try:
            with open(filename, "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print(f"Warning: {filename} not found. Using default styling.")
    
    def reload_stylesheet(self):
        print("Reloading stylesheet...")
        self.load_stylesheet("style_dark.qss" if self.theme_selector.currentText() == "Dark" else "style_light.qss")
    
    def change_theme(self, index):
        theme = "style_dark.qss" if index == 0 else "style_light.qss"
        self.qss_watcher.addPath(theme)
        self.load_stylesheet(theme)
        
class Card(QFrame):
    def __init__(self, parent=None, default_folder=""):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        self.parent = parent  
        
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link here...")
        
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Selected folder...")
        self.folder_input.setReadOnly(True)
        
        if default_folder:
            self.folder_input.setText(default_folder)
        
        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.open_folder_dialog)
        
        self.delete_button = QPushButton("X")
        self.delete_button.clicked.connect(self.delete_card)
        
        top_layout.addWidget(self.url_input)
        top_layout.addWidget(self.folder_input)
        top_layout.addWidget(self.folder_button)
        top_layout.addWidget(self.delete_button)
        
        self.switch = QCheckBox("Partial")
        self.switch.stateChanged.connect(self.toggle_partial_fields)
        self.quality_selector = QComboBox()
        self.quality_selector.addItems(["1080p", "720p", "480p", "360p", "240p", "144p"])
        
        self.partial_fields = QGridLayout()
        self.from_label = QLabel("From:")
        self.from_input = QLineEdit()
        self.to_label = QLabel("To:")
        self.to_input = QLineEdit()
        
        self.partial_fields.addWidget(self.from_label, 0, 0)
        self.partial_fields.addWidget(self.from_input, 0, 1)
        self.partial_fields.addWidget(self.to_label, 1, 0)
        self.partial_fields.addWidget(self.to_input, 1, 1)
        
        self.partial_fields_widget = QWidget()
        self.partial_fields_widget.setLayout(self.partial_fields)
        self.partial_fields_widget.setVisible(False)
        
        self.download_button = QPushButton("Download")
        self.download_button.setVisible(False)
        self.download_button.clicked.connect(self.start_download)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        layout.addLayout(top_layout)
        layout.addWidget(self.download_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.quality_selector)

        self.url_input.textChanged.connect(self.update_download_button)
        self.switch.stateChanged.connect(self.update_download_button)
        self.from_input.textChanged.connect(self.update_download_button)
        self.to_input.textChanged.connect(self.update_download_button)
        layout.addWidget(self.switch)
        layout.addWidget(self.partial_fields_widget)
        layout.addWidget(self.download_button)
    
    def open_folder_dialog(self):
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_input.setText(folder_path)
            self.parent.last_selected_folder = folder_path  
            self.parent.save_last_selected_folder()  
    
    def toggle_partial_fields(self):
        self.partial_fields_widget.setVisible(self.switch.isChecked())
        self.update_download_button()
    
    def update_download_button(self):
        url_valid = bool(self.url_input.text().strip())
        folder_valid = bool(self.folder_input.text().strip())
        
        if self.switch.isChecked():
            from_valid = is_valid_time_format(self.from_input.text())
            to_valid = is_valid_time_format(self.to_input.text())
            self.download_button.setVisible(url_valid and folder_valid and from_valid and to_valid)
        else:
            self.download_button.setVisible(url_valid and folder_valid)
    
    def start_download(self):
        ffmpeg_args = trim_args(self.from_input.text(),self.to_input.text())
        print("folder to download into",self.folder_input.text())
        opts = { #sometimes this mother fker can force the mp4 some time snot
            "outtmpl": self.folder_input.text() +"input", #webm seems to be the most comfortable format to be downloaded in 
            "external_downloader": ffmpeg_path,  # Use FFmpeg from venv
            "external_downloader_args": ffmpeg_args,
            "format": "bestvideo[height<="+self.quality_selector.currentText()[:-1]+"]+bestaudio/best",
            "writesubtitles": False,
            "writeautomaticsub": False,
            "--merge-output-format": "mp4",
            #lets keep it non quite for now
            #"quiet": True,  # Suppresses output  
            #"nocheckcertificate": True,  # Avoids SSL warnings  
            #"ignoreerrors": True  # Prevents it from stopping on minor errors  
        }
        url = self.url_input.text().strip()
        if not url:
            return
        with yt_dlp.YoutubeDL(opts) as ydl:
            global isDownloading 
            isDownloading = True
            ydl.download(url)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

    
    def delete_card(self):
        self.setParent(None)
        self.deleteLater()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeTrimmer()
    window.show()
    sys.exit(app.exec())