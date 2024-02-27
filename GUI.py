from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, 
    QFrame, QHBoxLayout, QLineEdit, QLabel, QCheckBox, QGridLayout, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QFileSystemWatcher
import sys
import os

class YouTubeTrimmer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Trimmer Tool")
        self.setGeometry(100, 100, 420, 550)
        
        self.last_selected_folder = self.get_default_download_folder()  # Store the last selected folder

        # Theme selection
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark", "Light"])
        self.theme_selector.currentIndexChanged.connect(self.change_theme)
        
        # File system watcher to monitor QSS file changes
        self.qss_watcher = QFileSystemWatcher(self)
        self.qss_watcher.fileChanged.connect(self.reload_stylesheet)
        
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.theme_selector)
        
        self.add_button = QPushButton("+ Add Card")
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
        
        self.change_theme(0)  # Load default theme
    
    def get_default_download_folder(self):
        """Returns the default downloads folder for both Windows and Linux"""
        if sys.platform == "win32":
            return os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            return os.path.join(os.path.expanduser("~"), "Downloads")
    
    def add_card(self):
        card = Card(self, self.last_selected_folder)
        self.scroll_layout.addWidget(card)
    
    def load_stylesheet(self, filename):
        try:
            with open(filename, "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print(f"Warning: {filename} not found. Using default styling.")
    
    def reload_stylesheet(self):
        """Reload styles when the QSS file changes"""
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
        self.parent = parent  # Store reference to main window
        
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
        
        layout.addLayout(top_layout)
        layout.addWidget(self.switch)
        layout.addWidget(self.partial_fields_widget)
        
    def open_folder_dialog(self):
        folder_dialog = QFileDialog()
        folder_path = folder_dialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_input.setText(folder_path)
            self.parent.last_selected_folder = folder_path  # Update last selected folder in main window
        
    def toggle_partial_fields(self):
        self.partial_fields_widget.setVisible(self.switch.isChecked())
        
    def delete_card(self):
        self.setParent(None)
        self.deleteLater()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeTrimmer()
    window.show()
    sys.exit(app.exec())
