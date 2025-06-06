from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QSpinBox, QDialogButtonBox, QGroupBox,
                            QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt

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
        self.parent = parent
        self.urls = []

        self.setWindowTitle("Edit User" if edit_mode else "Add New User")
        self.setMinimumWidth(500)
        self.setup_ui()

        # If editing, populate fields with existing data
        if edit_mode and user:
            self.username_input.setText(user.username)
            self.password_input.setText(user.password)
            self.url_input.setText(user.url)
            self.hours_input.setValue(user.hours)

            # Add URLs to the list
            if hasattr(user, 'urls') and user.urls:
                for url_item in user.urls:
                    if isinstance(url_item, dict):
                        self.add_url_to_list(url_item.get('url'), url_item.get('hours', 0))
                    else:
                        self.add_url_to_list(url_item, 0)

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

        # Primary URL field (for login)
        url_layout = QHBoxLayout()
        url_label = QLabel("Primary URL (Login URL):")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter the URL used for login")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        user_layout.addLayout(url_layout)

        # URLs section with hours (for learning, not for login)
        urls_group = QGroupBox("URLs with Study Hours (Learning URLs)")
        urls_layout = QVBoxLayout()

        # URL list
        self.url_list = QListWidget()
        urls_layout.addWidget(self.url_list)

        # Add URL section
        url_add_layout = QHBoxLayout()

        # New URL input (for learning)
        self.new_url_input = QLineEdit()
        self.new_url_input.setPlaceholderText("Enter learning URL to add (not login URL)")
        url_add_layout.addWidget(self.new_url_input)

        # Hours input for new URL
        self.new_url_hours = QSpinBox()
        self.new_url_hours.setMinimum(0)
        self.new_url_hours.setMaximum(9999)
        self.new_url_hours.setPrefix("Hours: ")
        url_add_layout.addWidget(self.new_url_hours)

        # Add URL button
        self.add_url_button = QPushButton("Add URL")
        self.add_url_button.clicked.connect(self.add_url)
        url_add_layout.addWidget(self.add_url_button)

        # Remove URL button
        self.remove_url_button = QPushButton("Remove URL")
        self.remove_url_button.clicked.connect(self.remove_url)
        url_add_layout.addWidget(self.remove_url_button)

        urls_layout.addLayout(url_add_layout)
        urls_group.setLayout(urls_layout)
        user_layout.addWidget(urls_group)

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


        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def add_url(self):
        """Add a URL to the list with hours"""
        url = self.new_url_input.text().strip()
        hours = self.new_url_hours.value()
        if url:
            # Check if URL is already in the list
            url_exists = False
            for url_item in self.urls:
                if isinstance(url_item, dict) and url_item.get('url') == url:
                    url_exists = True
                    break
                elif isinstance(url_item, str) and url_item == url:
                    url_exists = True
                    break

            if not url_exists:
                self.add_url_to_list(url, hours)
                self.new_url_input.clear()
                self.new_url_hours.setValue(0)

    def add_url_to_list(self, url, hours=0):
        """Add a URL to the list widget and internal list"""
        if url:
            # Check if URL is already in the list
            url_exists = False
            for url_item in self.urls:
                if isinstance(url_item, dict) and url_item.get('url') == url:
                    url_exists = True
                    break
                elif isinstance(url_item, str) and url_item == url:
                    url_exists = True
                    break

            if not url_exists:
                url_data = {'url': url, 'hours': hours}
                self.urls.append(url_data)
                display_text = f"{url} ({hours} hours)"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, url_data)  # Store the full data
                self.url_list.addItem(item)

    def remove_url(self):
        """Remove the selected URL from the list"""
        selected_items = self.url_list.selectedItems()
        if selected_items:
            for item in selected_items:
                # Get the URL from the item data
                url_data = item.data(Qt.UserRole)
                if url_data:
                    # Remove from the internal list
                    for i, url_item in enumerate(self.urls):
                        if isinstance(url_item, dict) and url_item.get('url') == url_data.get('url'):
                            del self.urls[i]
                            break
                else:
                    # Fallback to using the text (for backward compatibility)
                    url_text = item.text().split(' (')[0]  # Extract URL from display text
                    for i, url_item in enumerate(self.urls):
                        if isinstance(url_item, dict) and url_item.get('url') == url_text:
                            del self.urls[i]
                            break
                        elif isinstance(url_item, str) and url_item == url_text:
                            del self.urls[i]
                            break

                # Remove from the list widget
                self.url_list.takeItem(self.url_list.row(item))

    def get_user_data(self):
        """
        Get the user data entered in the dialog

        Returns:
            tuple: (username, password, url, hours, urls)
        """
        return (
            self.username_input.text(),
            self.password_input.text(),
            self.url_input.text(),
            self.hours_input.value(),
            self.urls
        )
