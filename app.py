from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFrame,
    QHBoxLayout, QLineEdit, QLabel, QCheckBox, QComboBox, QFileDialog,
    QFormLayout, QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import sys
import ctypes
import os
import json
import yt_dlp
import traceback
import imageio_ffmpeg  # Ensures FFmpeg is available in the venv
import re
from utils.trimmer import trim_args
from utils.conversion import Converter  
from utils.formatparser import get_format_option
from PyQt6.QtGui import QFont

vidConverter = Converter()
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
SETTINGS_FILE = "settings.json"

def load_stylesheet(filename):
    """Load QSS stylesheet from file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
        return ""

theme_styles = {
    "light": load_stylesheet("style_light.qss"),
    "dark": load_stylesheet("style_dark.qss")
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
    progress_updated = pyqtSignal(int)
    
    def __init__(self, url, opts, ui_state="", parent=None):
        super().__init__(parent)
        self.url = url
        self.opts = opts
        self.ui_state = ui_state
        self.last_progress = 0
        
    def progress_hook(self, d):
        """Hook for tracking download progress from yt_dlp."""
        try:
            if d['status'] == 'downloading':
                # Get the total bytes - try both regular and estimated
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                
                # Only calculate progress if we have a valid total
                if total > 0 and downloaded >= 0:
                    progress = int((downloaded / total) * 100)
                    # Only emit if progress changed by at least 1% to avoid too many signals
                    if progress != self.last_progress:
                        self.progress_updated.emit(progress)
                        self.last_progress = progress
            elif d['status'] == 'finished':
                self.progress_updated.emit(100)
                self.last_progress = 100
        except Exception as e:
            print(f"Progress hook error: {e}")
    
    def run(self):
        try:
            # Add progress hook to options
            self.opts['progress_hooks'] = [self.progress_hook]
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
        font = QFont()
        font.setPointSize(12)  # Set a valid font size
        self.download_overlay.setFont(font)
        overlay_layout = QVBoxLayout(self.download_overlay)
        overlay_layout.addStretch()
        self.downloading_label = QLabel("Downloading...", self.download_overlay)
        self.downloading_label.setStyleSheet("font-size: 20px; color: white;")
        self.downloading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.downloading_label.setFont(font)
        overlay_layout.addWidget(self.downloading_label)
        
        # Add progress bar
        self.download_progress = QProgressBar(self.download_overlay)
        self.download_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid white;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
            }
        """)
        self.download_progress.setMinimum(0)
        self.download_progress.setMaximum(100)
        self.download_progress.setValue(0)
        self.download_progress.setVisible(False)
        overlay_layout.addWidget(self.download_progress)
        
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
        stylesheet = theme_styles[self.current_theme]
        self.setStyleSheet(stylesheet)
        self.card.setStyleSheet(stylesheet)

    def show_download_overlay(self, text="Downloading..."):
        self.downloading_label.setText(text)
        # Ensure progress text is visible for determinate mode by default
        try:
            self.download_progress.setTextVisible(True)
        except Exception:
            pass
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.download_overlay.show()
    
    def hide_download_overlay(self):
        self.download_overlay.hide()
        self.download_progress.setVisible(False)
        self.download_progress.setValue(0)
        # Restore determinate range
        try:
            self.download_progress.setRange(0, 100)
            self.download_progress.setTextVisible(True)
        except Exception:
            pass
    
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

        # URL input
        url_row = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link here...")
        url_row.addWidget(url_label)
        url_row.addWidget(self.url_input)
        layout.addLayout(url_row)

        # Folder selection
        folder_row = QHBoxLayout()
        folder_label = QLabel("Output Folder:")
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Selected folder...")
        self.folder_input.setReadOnly(True)
        self.folder_input.setText(default_folder)
        self.folder_button = QPushButton("Select Folder")
        self.folder_button.clicked.connect(self.open_folder_dialog)
        folder_row.addWidget(folder_label)
        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(self.folder_button)
        layout.addLayout(folder_row)

        # Quality selector
        quality_row = QHBoxLayout()
        quality_label = QLabel("Quality:")
        self.quality_selector = QComboBox()
        self.quality_selector.addItems(["4320p", "2160p", "1440p","1080p", "720p", "480p", "360p", "240p", "144p", "audio-only"])
        from PyQt6.QtWidgets import QSizePolicy
        self.quality_selector.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        quality_row.addWidget(quality_label)
        quality_row.addWidget(self.quality_selector)
        quality_row.addStretch()
        layout.addLayout(quality_row)

        # Download name + exists indicator
        name_row = QHBoxLayout()
        name_label = QLabel("Download Name:")
        self.download_name_input = QLineEdit()
        self.download_name_input.setPlaceholderText("Enter filename for download")
        # Clickable indicator: shows 'File exists' and opens Explorer when clicked
        self.exists_indicator = QPushButton("File exists")
        self.exists_indicator.setFixedHeight(22)
        self.exists_indicator.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exists_indicator.setFlat(True)
        self.exists_indicator.setStyleSheet(
            "color: white; background-color: orange; border-radius: 4px; font-weight: bold; font-size: 11px; padding: 2px 6px;"
        )
        self.exists_indicator.setVisible(False)
        self._existing_full_path = None
        self.exists_indicator.clicked.connect(self.reveal_in_explorer)

        name_row.addWidget(name_label)
        name_row.addWidget(self.download_name_input)
        name_row.addWidget(self.exists_indicator)
        layout.addLayout(name_row)

        # Partial download switch
        self.switch = QCheckBox("Trim Video (Partial Download)")
        self.switch.stateChanged.connect(self.toggle_partial_fields)
        layout.addWidget(self.switch)

        # From/To fields
        self.from_label = QLabel("From:")
        self.from_label.setVisible(False)
        self.from_input = QLineEdit()
        self.from_input.setPlaceholderText("hh:mm:ss")
        self.from_input.setVisible(False)
        from_row = QHBoxLayout()
        from_row.addWidget(self.from_label)
        from_row.addWidget(self.from_input)
        self.from_layout = from_row
        layout.addLayout(from_row)

        self.to_label = QLabel("To:")
        self.to_label.setVisible(False)
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("hh:mm:ss")
        self.to_input.setVisible(False)
        to_row = QHBoxLayout()
        to_row.addWidget(self.to_label)
        to_row.addWidget(self.to_input)
        self.to_layout = to_row
        layout.addLayout(to_row)

        # Download button
        self.download_button = QPushButton("Download")
        self.download_button.setVisible(False)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)
        
        # Connect changes to update button visibility and indicator
        self.url_input.textChanged.connect(self.update_download_button)
        self.switch.stateChanged.connect(self.update_download_button)
        self.from_input.textChanged.connect(self.update_download_button)
        self.to_input.textChanged.connect(self.update_download_button)
        self.download_name_input.textChanged.connect(self.update_download_button)
        self.quality_selector.currentTextChanged.connect(self.update_download_button)
    def open_folder_dialog(self):      
        start_dir = self.folder_input.text().strip() or os.path.expanduser("~/Downloads")
        
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            start_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        if folder_path:
            self.folder_input.setText(folder_path)
            # Update the main window's last folder and save it
            self.parent().last_selected_folder = folder_path
            self.parent().save_last_selected_folder(folder_path)
            # refresh indicator for the new folder
            try:
                self.update_download_button()
            except Exception:
                pass
    
    def toggle_partial_fields(self):
        checked = self.switch.isChecked()
        self.from_input.setVisible(checked)
        self.to_input.setVisible(checked)
        self.from_label.setVisible(checked)
        self.to_label.setVisible(checked)
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

        # Update the exists indicator based on resolved output path
        try:
            download_name = self.download_name_input.text().strip() or "input"
            if self.quality_selector.currentText() == "audio-only":
                out_name = download_name if download_name.endswith(".wav") else download_name + ".wav"
            else:
                out_name = download_name if download_name.lower().endswith(".mp4") else download_name + ".mp4"
            folder = self.folder_input.text().strip() or ""
            full_path = os.path.abspath(os.path.normpath(os.path.join(folder, out_name))) if folder else None
            exists = os.path.exists(full_path) if full_path else False
        except Exception:
            exists = False
            full_path = None
        try:
            self._existing_full_path = full_path if exists else None
            self.exists_indicator.setVisible(bool(exists))
            self.exists_indicator.setEnabled(bool(exists))
            if exists and full_path:
                self.exists_indicator.setToolTip(full_path)
            else:
                self.exists_indicator.setToolTip("")
        except Exception:
            pass
    
    def start_download(self):
        if self.is_downloading:
            return
        self.is_downloading = True

        
        # Use the download name from the input field (default to "input" if empty)
        download_name = self.download_name_input.text().strip() or "input"
        if self.quality_selector.currentText() == "audio-only":
            # Ensure the output name ends with .wav for audio-only downloads
            out_name = download_name if download_name.endswith(".wav") else download_name + ".wav"
        else:
            out_name = download_name if download_name.lower().endswith(".mp4") else download_name + ".mp4"

        if self.switch.isChecked():
            global ffmpeg_path
            ffmpeg_args = trim_args(self.from_input.text().strip(), self.to_input.text().strip())
            opts = {
            "outtmpl": os.path.join(self.folder_input.text(), out_name),
            "external_downloader": ffmpeg_path,
            "external_downloader_args": ffmpeg_args,
            "format":  get_format_option(self.quality_selector.currentText()),
            "merge_output_format": "mp4",
        }
        else:
            opts = {
                "outtmpl": os.path.join(self.folder_input.text(), out_name),
                "format":  get_format_option(self.quality_selector.currentText()),
                "merge_output_format": "mp4",
            }
        #opts["cookiefile"] = "cookies.txt"

        url = self.url_input.text().strip()
        
        ui_state = self.get_ui_state()
        # Show the overlay from the parent (main window)
        # Use indeterminate progress when trimming (external ffmpeg downloader)
        if self.switch.isChecked():
            self.parent().show_download_overlay("Downloading & trimming")
            # Indeterminate/pulsing mode
            try:
                self.parent().download_progress.setRange(0, 0)
                self.parent().download_progress.setTextVisible(False)
            except Exception:
                # fallback
                self.parent().download_progress.setMinimum(0)
                self.parent().download_progress.setMaximum(0)
            self.parent().download_progress.setVisible(True)
        else:
            self.parent().show_download_overlay("Downloading...")
            # Determinate mode
            try:
                self.parent().download_progress.setRange(0, 100)
                self.parent().download_progress.setTextVisible(True)
            except Exception:
                self.parent().download_progress.setMinimum(0)
                self.parent().download_progress.setMaximum(100)
            self.parent().download_progress.setValue(0)
            self.parent().download_progress.setVisible(True)

        # Create and start the download thread
        self.download_thread = DownloadThread(url, opts, ui_state, parent=self)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.progress_updated.connect(self.parent().download_progress.setValue)
        self.download_thread.start()
    
    def reveal_in_explorer(self):
        """Open the OS file browser and select the existing file."""
        try:
            path = getattr(self, "_existing_full_path", None)
            if not path:
                return
            if os.name == "nt":
                # explorer expects the /select,<path> as a single argument
                subprocess.run(["explorer", f"/select,{path}"])
            else:
                # fallback: open containing folder
                folder = os.path.dirname(path)
                if folder:
                    if sys.platform == "darwin":
                        subprocess.run(["open", folder])
                    else:
                        subprocess.run(["xdg-open", folder])
        except Exception as e:
            print("Failed to reveal file:", e)
    
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
        self.conversion_thread = ConversionThread(input_base, self.folder_input.text(), output_fileName, deletesOriginal=False)
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
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mycompany.myapp")
    app = QApplication(sys.argv)
    default_font = QFont()
    default_font.setPointSize(12)  # Ensure the font size is valid
    app.setFont(default_font)
    app.setWindowIcon(QIcon("yttrimmerIcon.ico"))  # Set the app icon
    window = YouTubeTrimmer()
    window.show()
    sys.exit(app.exec())