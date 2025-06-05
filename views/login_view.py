
from PyQt5.QtWidgets import QMessageBox

class LoginView:
    def __init__(self, window):
        self.window = window

    def show_error(self, message):
        QMessageBox.warning(self.window, "Error", message)

    def show_success(self):
        QMessageBox.information(self.window, "Success", "Login successful!")
