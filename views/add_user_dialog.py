from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QSpinBox, QDialogButtonBox)

class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        """
        Initialize the dialog for adding a new user
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Add New User")
        self.setMinimumWidth(300)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface components"""
        layout = QVBoxLayout()
        
        # Username field
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Password field
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # URL field
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Hours field
        hours_layout = QHBoxLayout()
        hours_label = QLabel("Hours:")
        self.hours_input = QSpinBox()
        self.hours_input.setMinimum(0)
        self.hours_input.setMaximum(24)
        hours_layout.addWidget(hours_label)
        hours_layout.addWidget(self.hours_input)
        layout.addLayout(hours_layout)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self.setLayout(layout)
    
    def get_user_data(self):
        """
        Get the user data entered in the dialog
        
        Returns:
            tuple: (username, password, url, hours)
        """
        return (
            self.username_input.text(),
            self.password_input.text(),
            self.url_input.text(),
            self.hours_input.value()
        )