from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt

class AddCourseDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, course=None):
        """
        Initialize the dialog for adding or editing a course
        
        Args:
            parent: The parent widget
            edit_mode (bool): Whether this dialog is for editing an existing course
            course: The course to edit (if edit_mode is True)
        """
        super().__init__(parent)
        
        self.edit_mode = edit_mode
        self.course = course
        
        self.initUI()
        
    def initUI(self):
        """Set up the user interface"""
        # Set window title based on mode
        self.setWindowTitle("Edit Course" if self.edit_mode else "Add Course")
        
        # Main layout
        layout = QVBoxLayout()
        
        # Course name
        name_layout = QHBoxLayout()
        name_label = QLabel("Course Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Course URL
        url_layout = QHBoxLayout()
        url_label = QLabel("Course URL:")
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Current lesson URL (optional)
        lesson_layout = QHBoxLayout()
        lesson_label = QLabel("Current Lesson URL (optional):")
        self.lesson_input = QLineEdit()
        lesson_layout.addWidget(lesson_label)
        lesson_layout.addWidget(self.lesson_input)
        layout.addLayout(lesson_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.save_button = QPushButton("Save")
        
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.validate_and_accept)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # If editing, populate fields with existing data
        if self.edit_mode and self.course:
            self.name_input.setText(self.course.name)
            self.url_input.setText(self.course.url)
            self.lesson_input.setText(self.course.current_lesson)
            
    def validate_and_accept(self):
        """Validate the input and accept the dialog if valid"""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Course name cannot be empty")
            return
            
        if not url:
            QMessageBox.warning(self, "Validation Error", "Course URL cannot be empty")
            return
            
        # All validation passed
        self.accept()