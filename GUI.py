from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, 
    QFrame, QHBoxLayout, QLineEdit, QLabel, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt
import sys

class YouTubeTrimmer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Trimmer Tool")
        self.setGeometry(100, 100, 420, 550)
        self.setStyleSheet(self.get_styles())
        
        layout = QVBoxLayout(self)
        
        self.add_button = QPushButton("+ Add Card")
        self.add_button.setObjectName("addButton")
        self.add_button.clicked.connect(self.add_card)
        layout.addWidget(self.add_button)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)
        
    def add_card(self):
        card = Card(self)
        self.scroll_layout.addWidget(card)
    
    def get_styles(self):
        return """
        QWidget {
            background-color: #f8f9fa;
            font-family: Arial;
        }
        QPushButton#addButton {
            background-color: #007bff;
            color: white;
            padding: 8px;
            border-radius: 5px;
            font-size: 14px;
        }
        QPushButton#addButton:hover {
            background-color: #0056b3;
        }
        QFrame {
            background: white;
            border-radius: 10px;
            padding: 10px;
            border: 1px solid #ddd;
            margin: 5px;
        }
        QLineEdit {
            border: 1px solid #ced4da;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #dc3545;
            color: white;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
        """
        
class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link here...")
        self.delete_button = QPushButton("X")
        self.delete_button.clicked.connect(self.delete_card)
        
        top_layout.addWidget(self.url_input)
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
