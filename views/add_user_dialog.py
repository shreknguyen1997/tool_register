from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QSpinBox, QDialogButtonBox, QGroupBox)

class AddUserDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, user=None):
        """
        Initialize the dialog for adding or editing a user

        Args:
            parent: Parent widget
            edit_mode (bool): Whether this dialog is for editing an existing user
            user: The user to edit (if edit_mode is True)
        """
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.user = user

        self.setWindowTitle("Edit User" if edit_mode else "Add New User")
        self.setMinimumWidth(400)
        self.setup_ui()

        # If editing, populate fields with existing data
        if edit_mode and user:
            self.username_input.setText(user.username)
            self.password_input.setText(user.password)
            self.url_input.setText(user.url)
            self.hours_input.setValue(user.hours)

            # Try to get the first course for this user
            if parent and hasattr(parent, 'course_controller'):
                courses = parent.course_controller.get_courses_for_user(user.id)
                if courses:
                    self.course_url_input.setText(courses[0].url)
                    self.completion_time_input.setValue(courses[0].completion_time)

    def setup_ui(self):
        """Set up the user interface components"""
        layout = QVBoxLayout()

        # User Information Group
        user_group = QGroupBox("User Information")
        user_layout = QVBoxLayout()

        # Username field
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        user_layout.addLayout(username_layout)

        # Password field
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        user_layout.addLayout(password_layout)

        # URL field
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        user_layout.addLayout(url_layout)

        # Hours field
        hours_layout = QHBoxLayout()
        hours_label = QLabel("Hours:")
        self.hours_input = QSpinBox()
        self.hours_input.setMinimum(0)
        self.hours_input.setMaximum(24)
        hours_layout.addWidget(hours_label)
        hours_layout.addWidget(self.hours_input)
        user_layout.addLayout(hours_layout)

        user_group.setLayout(user_layout)
        layout.addWidget(user_group)

        # Course Information Group
        course_group = QGroupBox("Course Information")
        course_layout = QVBoxLayout()

        # Course URL field
        course_url_layout = QHBoxLayout()
        course_url_label = QLabel("Course URL:")
        self.course_url_input = QLineEdit()
        course_url_layout.addWidget(course_url_label)
        course_url_layout.addWidget(self.course_url_input)
        course_layout.addLayout(course_url_layout)

        # Course Completion Time field
        completion_time_layout = QHBoxLayout()
        completion_time_label = QLabel("Completion Time (hours):")
        self.completion_time_input = QSpinBox()
        self.completion_time_input.setMinimum(0)
        self.completion_time_input.setMaximum(9999)  # No max limit
        completion_time_layout.addWidget(completion_time_label)
        completion_time_layout.addWidget(self.completion_time_input)
        course_layout.addLayout(completion_time_layout)

        course_group.setLayout(course_layout)
        layout.addWidget(course_group)

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
            tuple: (username, password, url, hours, course_url, completion_time)
        """
        return (
            self.username_input.text(),
            self.password_input.text(),
            self.url_input.text(),
            self.hours_input.value(),
            self.course_url_input.text(),
            self.completion_time_input.value()
        )
