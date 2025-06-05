
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
                            QLineEdit, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox,
                            QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, 
                            QAbstractItemView, QFrame, QToolButton)
from PyQt5.QtCore import Qt, QSize, QTimer
from controllers.login_controller import LoginController
from controllers.user_controller import UserController
from models.login_model import LoginModel
from views.login_view import LoginView
from models.user_model import User
from models.database_model import DatabaseModel
from views.add_user_dialog import AddUserDialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Khởi tạo các thành phần MVC cho login
        self.login_model = LoginModel()  # Không cần đường dẫn ChromeDriver nữa vì đã sử dụng requests
        self.login_view = LoginView(self)
        self.login_controller = LoginController(self.login_model, self.login_view)

        # Khởi tạo kết nối database MySQL
        self.db_model = DatabaseModel()

        # Khởi tạo controller cho quản lý người dùng
        self.user_controller = UserController(self.db_model, self)

        # Khởi tạo danh sách người dùng từ database
        self.users = self.user_controller.get_all_users()

        # Khởi tạo timer để cập nhật thời gian chạy
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_running_time)
        self.timer.start(1000)  # Cập nhật mỗi giây

        # Nếu database trống, thêm một số người dùng mẫu
        if not self.users:
            sample_users = [
                ("user1", "password1", "https://example.com", 1),
                ("user2", "password2", "https://example.org", 2),
                ("001097034799", "", "https://hoclythuyetlaixe.eco-tek.com.vn/web/login", 1)  # Thêm tài khoản cho trang hoclythuyetlaixe
            ]
            for username, password, url, hours in sample_users:
                success, _, _ = self.user_controller.add_user(username, password, url, hours)

            # Lấy lại danh sách từ database
            self.users = self.user_controller.get_all_users()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("User Management and Login Automation")

        # Đặt kích thước cửa sổ lớn hơn
        self.setGeometry(100, 100, 900, 600)

        # Giao diện chính
        self.layout = QVBoxLayout()

        # Tiêu đề và thanh tìm kiếm
        header_layout = QHBoxLayout()

        self.label = QLabel("User List:")
        header_layout.addWidget(self.label)

        # Thêm thanh tìm kiếm
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.filter_users)
        header_layout.addWidget(self.search_input)

        self.layout.addLayout(header_layout)

        # Bảng dữ liệu người dùng
        self.user_table = QTableWidget(self)
        self.user_table.setColumnCount(7)  # Checkbox, Username, URL, Hours, Status, Running Time, Actions
        self.user_table.setHorizontalHeaderLabels(["", "Username", "URL", "Hours", "Status", "Running Time", "Actions"])

        # Cấu hình bảng
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox column
        self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Username column
        self.user_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # URL column
        self.user_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Hours column
        self.user_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status column
        self.user_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Running Time column
        self.user_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Actions column

        # Kết nối sự kiện chọn dòng trong bảng
        self.user_table.itemClicked.connect(self.user_selected)

        self.layout.addWidget(self.user_table)

        # Footer
        footer_frame = QFrame()
        footer_frame.setFrameShape(QFrame.HLine)
        footer_frame.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(footer_frame)

        footer_layout = QHBoxLayout()
        self.status_label = QLabel("Total users: 0")
        footer_layout.addWidget(self.status_label)

        # Spacer to push buttons to the right
        footer_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Nút xóa người dùng đã chọn
        self.delete_selected_button = QPushButton("Delete Selected", self)
        self.delete_selected_button.clicked.connect(self.delete_selected_users)
        footer_layout.addWidget(self.delete_selected_button)

        # Nút thêm người dùng
        self.add_button = QPushButton("Add User", self)
        self.add_button.clicked.connect(self.add_user)
        footer_layout.addWidget(self.add_button)

        self.layout.addLayout(footer_layout)

        # Phần chạy tự động
        run_layout = QHBoxLayout()

        # Spacer to push buttons to the right
        run_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Thêm nút Run Selected (chạy tất cả người dùng đã chọn)
        self.run_selected_button = QPushButton("Run Selected", self)
        self.run_selected_button.clicked.connect(self.run_selected_users)
        run_layout.addWidget(self.run_selected_button)

        # Thêm nút Run (chạy người dùng đang chọn)
        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.handle_login)
        run_layout.addWidget(self.run_button)

        self.layout.addLayout(run_layout)

        # Lưu trữ URL của người dùng đang chọn (không hiển thị trong UI)
        self.url_input = QLineEdit(self)
        self.url_input.setVisible(False)

        # Cập nhật danh sách người dùng
        self.update_user_list()

        # Thêm một khoảng trống để căn chỉnh giao diện
        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)

        self.setLayout(self.layout)

        # Lưu trữ username và password của người dùng đã chọn (không hiển thị)
        self.selected_username = ""
        self.selected_password = ""

    def update_user_list(self):
        """Cập nhật danh sách người dùng trong table widget"""
        self.user_table.setRowCount(0)  # Clear the table

        for row, user in enumerate(self.users):
            self.user_table.insertRow(row)

            # Checkbox column
            checkbox = QCheckBox()
            checkbox_cell = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_cell)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.user_table.setCellWidget(row, 0, checkbox_cell)

            # Username column
            username_item = QTableWidgetItem(user.username)
            self.user_table.setItem(row, 1, username_item)

            # URL column
            url_item = QTableWidgetItem(user.url)
            self.user_table.setItem(row, 2, url_item)

            # Hours column
            hours_item = QTableWidgetItem(str(user.hours))
            hours_item.setTextAlignment(Qt.AlignCenter)
            self.user_table.setItem(row, 3, hours_item)

            # Status column
            status_item = QTableWidgetItem(user.status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.user_table.setItem(row, 4, status_item)

            # Running Time column
            running_time_text = self.format_running_time(user.running_time)
            running_time_item = QTableWidgetItem(running_time_text)
            running_time_item.setTextAlignment(Qt.AlignCenter)
            self.user_table.setItem(row, 5, running_time_item)

            # Actions column
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            # Edit button
            edit_button = QToolButton()
            edit_button.setText("Edit")
            edit_button.setToolTip("Edit user")
            edit_button.clicked.connect(lambda checked, r=row: self.edit_user(r))

            # Delete button
            delete_button = QToolButton()
            delete_button.setText("Delete")
            delete_button.setToolTip("Delete user")
            delete_button.clicked.connect(lambda checked, r=row: self.delete_user(r))

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.user_table.setCellWidget(row, 6, actions_cell)

        # Update footer status
        self.status_label.setText(f"Total users: {len(self.users)}")

    def format_running_time(self, seconds):
        """Format running time in seconds to a human-readable format"""
        if seconds == 0:
            return "0m"

        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"

    def filter_users(self, text):
        """Filter users based on search text"""
        if not text:
            # If search text is empty, show all users
            self.users = self.user_controller.get_all_users()
        else:
            # Search in database
            self.users = self.user_controller.search_users(text)

        # Update the table with filtered users
        self.update_user_list()

    def add_user(self):
        """Hiển thị dialog thêm người dùng và xử lý kết quả"""
        dialog = AddUserDialog(self)
        if dialog.exec_():
            # Nếu người dùng nhấn OK
            username, password, url, hours = dialog.get_user_data()

            # Thêm người dùng thông qua controller
            success, user_id, message = self.user_controller.add_user(username, password, url, hours)

            if success:
                # Cập nhật danh sách người dùng từ database
                self.users = self.user_controller.get_all_users()

                # Cập nhật danh sách hiển thị
                self.update_user_list()

                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Input Error" if "fields" in message else "Database Error", message)

    def delete_user(self, row=None):
        """Xóa người dùng đã chọn khỏi danh sách"""
        # Nếu row được truyền vào (từ nút Delete trong bảng)
        if row is not None:
            current_row = row
        else:
            # Lấy dòng đang chọn từ bảng
            current_row = self.user_table.currentRow()

        if current_row >= 0 and current_row < len(self.users):
            # Xác nhận xóa
            user = self.users[current_row]
            reply = QMessageBox.question(self, "Confirm Delete", 
                                        f"Are you sure you want to delete user {user.username}?",
                                        QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.Yes:
                # Xóa người dùng thông qua controller
                success, message = self.user_controller.delete_user(user.id)

                if success:
                    # Cập nhật danh sách người dùng từ database
                    self.users = self.user_controller.get_all_users()

                    # Cập nhật danh sách hiển thị
                    self.update_user_list()

                    # Xóa thông tin trong trường URL và biến lưu trữ
                    self.url_input.clear()
                    self.selected_username = ""
                    self.selected_password = ""

                    QMessageBox.information(self, "Success", message)
                else:
                    QMessageBox.warning(self, "Database Error", message)
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a valid user to delete!")

    def user_selected(self, item):
        """Xử lý khi người dùng chọn một người dùng từ bảng"""
        current_row = item.row()
        current_col = item.column()

        # Nếu người dùng click vào cột checkbox, không cần xử lý gì thêm
        if current_col == 0:
            return

        if current_row >= 0:
            user = self.users[current_row]

            # Lưu thông tin đăng nhập
            self.url_input.setText(user.url)
            self.selected_username = user.username
            self.selected_password = user.password

    def start_user(self, user):
        """Bắt đầu chạy một user (đánh dấu là đang chạy)"""
        # Cập nhật trạng thái user thành "running"
        user.status = "running"

        # Cập nhật vào database
        self.user_controller.update_user(
            user.id, 
            user.username, 
            user.password, 
            user.url, 
            user.hours, 
            user.status, 
            user.running_time
        )

        # Cập nhật giao diện
        self.update_user_list()

    def stop_user(self, user):
        """Dừng chạy một user (đánh dấu là đã dừng)"""
        # Cập nhật trạng thái user thành "stopped"
        user.status = "stopped"

        # Cập nhật vào database
        self.user_controller.update_user(
            user.id, 
            user.username, 
            user.password, 
            user.url, 
            user.hours, 
            user.status, 
            user.running_time
        )

        # Cập nhật giao diện
        self.update_user_list()

    def handle_login(self):
        """Xử lý chạy tự động với thông tin người dùng đã chọn"""
        url = self.url_input.text()

        # Kiểm tra xem đã chọn người dùng chưa
        if not url or not self.selected_username or not self.selected_password:
            QMessageBox.warning(self, "Selection Error", "Please select a user first!")
            return

        # Tìm user đang được chọn
        current_row = self.user_table.currentRow()
        if current_row >= 0 and current_row < len(self.users):
            user = self.users[current_row]

            # Đánh dấu user là đang chạy
            self.start_user(user)

            # Gọi login_controller để xử lý đăng nhập
            success = self.login_controller.handle_login(url, self.selected_username, self.selected_password)

            # Nếu đăng nhập thất bại, đánh dấu user là đã dừng
            if not success:
                self.stop_user(user)

    def edit_user(self, row):
        """Chỉnh sửa thông tin người dùng"""
        if row >= 0 and row < len(self.users):
            user = self.users[row]

            # Tạo dialog với thông tin người dùng hiện tại
            dialog = AddUserDialog(self)
            dialog.username_input.setText(user.username)
            dialog.password_input.setText(user.password)
            dialog.url_input.setText(user.url)
            dialog.hours_input.setValue(user.hours)

            if dialog.exec_():
                # Nếu người dùng nhấn OK
                username, password, url, hours = dialog.get_user_data()

                # Cập nhật thông tin người dùng thông qua controller
                success, message = self.user_controller.update_user(user.id, username, password, url, hours)

                if success:
                    # Cập nhật danh sách người dùng từ database
                    self.users = self.user_controller.get_all_users()

                    # Cập nhật danh sách hiển thị
                    self.update_user_list()

                    QMessageBox.information(self, "Success", message)
                else:
                    QMessageBox.warning(self, "Input Error" if "fields" in message else "Database Error", message)

    def get_selected_users(self):
        """Lấy danh sách người dùng đã chọn (đánh dấu checkbox)"""
        selected_users = []
        for row in range(self.user_table.rowCount()):
            # Lấy widget chứa checkbox
            checkbox_widget = self.user_table.cellWidget(row, 0)
            if checkbox_widget:
                # Lấy checkbox từ layout của widget
                checkbox = checkbox_widget.layout().itemAt(0).widget()
                if checkbox.isChecked():
                    selected_users.append((row, self.users[row]))
        return selected_users

    def delete_selected_users(self):
        """Xóa tất cả người dùng đã chọn"""
        selected_users = self.get_selected_users()

        if not selected_users:
            QMessageBox.warning(self, "Selection Error", "Please select at least one user to delete!")
            return

        # Xác nhận xóa
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Are you sure you want to delete {len(selected_users)} selected users?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Lấy danh sách ID người dùng đã chọn
            user_ids = [user.id for _, user in selected_users]

            # Xóa người dùng thông qua controller
            success_count, total_count, message = self.user_controller.delete_selected_users(user_ids)

            if success_count > 0:
                # Cập nhật danh sách người dùng từ database
                self.users = self.user_controller.get_all_users()

                # Cập nhật danh sách hiển thị
                self.update_user_list()

                # Xóa thông tin trong biến lưu trữ
                self.url_input.clear()
                self.selected_username = ""
                self.selected_password = ""

                QMessageBox.information(self, "Success", message)

            if success_count < total_count:
                QMessageBox.warning(self, "Partial Success", message)

    def run_selected_users(self):
        """Chạy tất cả người dùng đã chọn"""
        selected_users = self.get_selected_users()

        if not selected_users:
            QMessageBox.warning(self, "Selection Error", "Please select at least one user to run!")
            return

        # Thông báo số lượng người dùng sẽ được chạy
        reply = QMessageBox.question(self, "Confirm Run", 
                                    f"Are you sure you want to run {len(selected_users)} selected users?",
                                    QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Chạy lần lượt từng người dùng
            for _, user in selected_users:
                self.login_controller.handle_login(user.url, user.username, user.password)

            QMessageBox.information(self, "Success", f"Completed running {len(selected_users)} users!")

    def update_running_time(self):
        """Cập nhật thời gian chạy cho các user có trạng thái 'running'"""
        updated = False
        for user in self.users:
            if user.status == "running":
                user.running_time += 1
                # Cập nhật vào database
                self.user_controller.update_user(
                    user.id, 
                    user.username, 
                    user.password, 
                    user.url, 
                    user.hours, 
                    user.status, 
                    user.running_time
                )
                updated = True

        # Nếu có user được cập nhật, refresh table
        if updated:
            self.update_user_list()

    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        # Dừng timer
        if hasattr(self, 'timer'):
            self.timer.stop()

        # Đóng kết nối database thông qua controller
        if hasattr(self, 'user_controller'):
            self.user_controller.close_connection()
        event.accept()

# Chạy ứng dụng PyQt5
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
