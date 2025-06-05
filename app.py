import sys
import os
import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
                            QLineEdit, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox,
                            QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, 
                            QAbstractItemView, QFrame, QToolButton, QTabWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from selenium.webdriver.common.by import By
from controllers.login_controller import LoginController
from controllers.user_controller import UserController
from controllers.course_controller import CourseController
from models.login_model import LoginModel
from views.login_view import LoginView
from models.user_model import User
from models.course_model import Course
from models.database_model import DatabaseModel
from views.add_user_dialog import AddUserDialog
from views.add_course_dialog import AddCourseDialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Khởi tạo các thành phần MVC cho login
        # Sử dụng đường dẫn tương đối để tìm ChromeDriver
        current_dir = os.path.dirname(os.path.abspath(__file__))
        driver_path = os.path.join(current_dir, "chromedriver", "chromedriver")
        print(f"ChromeDriver path: {driver_path}")
        self.login_model = LoginModel(driver_path)  # Đảm bảo luôn sử dụng Selenium WebDriver
        self.login_view = LoginView(self)
        self.login_controller = LoginController(self.login_model, self.login_view)

        # Khởi tạo kết nối database MySQL
        self.db_model = DatabaseModel()

        # Khởi tạo controller cho quản lý người dùng
        self.user_controller = UserController(self.db_model, self)

        # Khởi tạo controller cho quản lý khóa học
        self.course_controller = CourseController(self.db_model, self)

        # Khởi tạo danh sách người dùng từ database
        self.users = self.user_controller.get_all_users()

        # Khởi tạo danh sách khóa học (sẽ được cập nhật khi chọn user)
        self.courses = []

        # Lưu trữ trạng thái checkbox cho mỗi user và course
        self.checkbox_states = {}  # Dictionary để lưu trạng thái checkbox: {user_id: is_checked}
        self.course_checkbox_states = {}  # Dictionary để lưu trạng thái checkbox cho courses: {course_id: is_checked}

        # Lưu trữ user và course đang được chọn
        self.selected_user = None
        self.selected_course = None

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
        self.setGeometry(100, 100, 1000, 700)

        # Giao diện chính
        self.layout = QVBoxLayout()

        # Tạo tab widget để chứa các tab
        self.tab_widget = QTabWidget()

        # Tạo tab cho quản lý người dùng
        self.user_tab = QWidget()
        self.setup_user_tab()
        self.tab_widget.addTab(self.user_tab, "Users")

        # Tạo tab cho quản lý khóa học
        self.course_tab = QWidget()
        self.setup_course_tab()
        self.tab_widget.addTab(self.course_tab, "Courses")

        # Thêm tab widget vào layout chính
        self.layout.addWidget(self.tab_widget)

        # Phần chạy tự động
        run_layout = QHBoxLayout()

        # Spacer to push buttons to the right
        run_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Thêm nút Stop All (dừng tất cả người dùng đang chạy)
        self.stop_all_button = QPushButton("Stop All", self)
        self.stop_all_button.clicked.connect(self.stop_all_users)
        run_layout.addWidget(self.stop_all_button)

        # Thêm nút Stop Selected (dừng tất cả người dùng đã chọn và đang chạy)
        self.stop_selected_button = QPushButton("Stop Selected", self)
        self.stop_selected_button.clicked.connect(self.stop_selected_users)
        run_layout.addWidget(self.stop_selected_button)

        # Thêm nút Run All (chạy tất cả người dùng)
        self.run_all_button = QPushButton("Run All", self)
        self.run_all_button.clicked.connect(self.run_all_users)
        run_layout.addWidget(self.run_all_button)

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

        self.setLayout(self.layout)

        # Lưu trữ username và password của người dùng đã chọn (không hiển thị)
        self.selected_username = ""
        self.selected_password = ""

    def setup_user_tab(self):
        """Thiết lập giao diện tab quản lý người dùng"""
        user_layout = QVBoxLayout()

        # Tiêu đề và thanh tìm kiếm
        header_layout = QHBoxLayout()

        self.label = QLabel("User List:")
        header_layout.addWidget(self.label)

        # Thêm thanh tìm kiếm
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.filter_users)
        header_layout.addWidget(self.search_input)

        user_layout.addLayout(header_layout)

        # Bảng dữ liệu người dùng
        self.user_table = QTableWidget(self)
        self.user_table.setColumnCount(8)  # Checkbox, Username, URL, Hours, Status, Running Time, Courses, Actions
        self.user_table.setHorizontalHeaderLabels(["", "Username", "URL", "Hours", "Status", "Running Time", "Courses", "Actions"])

        # Cấu hình bảng
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox column
        self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Username column
        self.user_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # URL column
        self.user_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Hours column
        self.user_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status column
        self.user_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Running Time column
        self.user_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Courses column
        self.user_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Actions column

        # Kết nối sự kiện chọn dòng trong bảng
        self.user_table.itemClicked.connect(self.user_selected)

        user_layout.addWidget(self.user_table)

        # Footer
        footer_frame = QFrame()
        footer_frame.setFrameShape(QFrame.HLine)
        footer_frame.setFrameShadow(QFrame.Sunken)
        user_layout.addWidget(footer_frame)

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

        user_layout.addLayout(footer_layout)

        # Cập nhật danh sách người dùng
        self.update_user_list()

        # Thiết lập layout cho tab
        self.user_tab.setLayout(user_layout)

    def setup_course_tab(self):
        """Thiết lập giao diện tab quản lý khóa học"""
        course_layout = QVBoxLayout()

        # Tiêu đề và thông tin
        header_layout = QHBoxLayout()
        self.course_label = QLabel("Courses for selected user:")
        header_layout.addWidget(self.course_label)

        # Spacer to push info to the right
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Thông tin người dùng đang chọn
        self.selected_user_label = QLabel("No user selected")
        header_layout.addWidget(self.selected_user_label)

        course_layout.addLayout(header_layout)

        # Bảng dữ liệu khóa học
        self.course_table = QTableWidget(self)
        self.course_table.setColumnCount(6)  # Checkbox, Name, URL, Current Lesson, Completed, Actions
        self.course_table.setHorizontalHeaderLabels(["", "Name", "URL", "Current Lesson", "Completed", "Actions"])

        # Cấu hình bảng
        self.course_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.course_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.course_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Checkbox column
        self.course_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Name column
        self.course_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # URL column
        self.course_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Current Lesson column
        self.course_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Completed column
        self.course_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Actions column

        # Kết nối sự kiện chọn dòng trong bảng
        self.course_table.itemClicked.connect(self.course_selected)

        course_layout.addWidget(self.course_table)

        # Footer
        footer_frame = QFrame()
        footer_frame.setFrameShape(QFrame.HLine)
        footer_frame.setFrameShadow(QFrame.Sunken)
        course_layout.addWidget(footer_frame)

        footer_layout = QHBoxLayout()
        self.course_status_label = QLabel("Total courses: 0")
        footer_layout.addWidget(self.course_status_label)

        # Spacer to push buttons to the right
        footer_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Nút xóa khóa học đã chọn
        self.delete_selected_courses_button = QPushButton("Delete Selected", self)
        self.delete_selected_courses_button.clicked.connect(self.delete_selected_courses)
        footer_layout.addWidget(self.delete_selected_courses_button)

        # Nút thêm khóa học
        self.add_course_button = QPushButton("Add Course", self)
        self.add_course_button.clicked.connect(self.add_course)
        footer_layout.addWidget(self.add_course_button)

        course_layout.addLayout(footer_layout)

        # Thiết lập layout cho tab
        self.course_tab.setLayout(course_layout)

    def update_user_list(self):
        """Cập nhật danh sách người dùng trong table widget"""
        # Lưu trạng thái checkbox hiện tại trước khi cập nhật bảng
        self.save_checkbox_states()

        self.user_table.setRowCount(0)  # Clear the table

        for row, user in enumerate(self.users):
            self.user_table.insertRow(row)

            # Checkbox column - Direct checkbox for better click handling
            checkbox = QCheckBox()
            # Khôi phục trạng thái checkbox từ dictionary
            is_checked = self.checkbox_states.get(user.id, False)
            checkbox.setChecked(is_checked)

            # Kết nối sự kiện stateChanged để cập nhật dictionary khi checkbox thay đổi
            checkbox.stateChanged.connect(lambda state, user_id=user.id: self.on_checkbox_changed(state, user_id))

            # Center the checkbox
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(checkbox)
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            # Make sure the widget is clickable
            cell_widget.setFocusPolicy(Qt.StrongFocus)
            self.user_table.setCellWidget(row, 0, cell_widget)

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

            # Courses column (completion ratio)
            _, _, ratio_text = self.course_controller.get_completion_ratio(user.id)
            courses_item = QTableWidgetItem(ratio_text)
            courses_item.setTextAlignment(Qt.AlignCenter)
            self.user_table.setItem(row, 6, courses_item)

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
            self.user_table.setCellWidget(row, 7, actions_cell)

        # Update footer status
        self.status_label.setText(f"Total users: {len(self.users)}")

    def add_course(self):
        """Mở dialog thêm khóa học mới"""
        # Kiểm tra xem đã chọn user chưa
        if not self.selected_user:
            QMessageBox.warning(self, "Selection Error", "Please select a user first!")
            return

        dialog = AddCourseDialog(self)
        if dialog.exec_():
            name = dialog.name_input.text().strip()
            url = dialog.url_input.text().strip()
            current_lesson = dialog.lesson_input.text().strip()

            success, message, course_id = self.course_controller.add_course(
                self.selected_user.id, name, url, current_lesson)

            if success:
                # Cập nhật danh sách khóa học
                self.update_course_list()
                QMessageBox.information(self, "Success", "Course added successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add course: {message}")

    def edit_course(self, row):
        """Mở dialog chỉnh sửa thông tin khóa học"""
        if row >= 0 and row < len(self.courses):
            course = self.courses[row]
            dialog = AddCourseDialog(self, edit_mode=True, course=course)

            if dialog.exec_():
                name = dialog.name_input.text().strip()
                url = dialog.url_input.text().strip()
                current_lesson = dialog.lesson_input.text().strip()

                success, message = self.course_controller.update_course(
                    course.id, name, url, current_lesson)

                if success:
                    # Cập nhật danh sách khóa học
                    self.update_course_list()
                    QMessageBox.information(self, "Success", "Course updated successfully!")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to update course: {message}")

    def delete_course(self, row):
        """Xóa một khóa học"""
        if row >= 0 and row < len(self.courses):
            course = self.courses[row]

            # Xác nhận xóa
            confirm = QMessageBox.question(self, "Confirm Deletion", 
                                          f"Are you sure you want to delete course '{course.name}'?",
                                          QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                success, message = self.course_controller.delete_course(course.id)

                if success:
                    # Cập nhật danh sách khóa học
                    self.update_course_list()
                    QMessageBox.information(self, "Success", "Course deleted successfully!")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete course: {message}")

    def delete_selected_courses(self):
        """Xóa tất cả khóa học đã chọn (đánh dấu checkbox)"""
        selected_rows = []
        for row in range(self.course_table.rowCount()):
            checkbox_widget = self.course_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_layout = checkbox_widget.layout()
                checkbox = checkbox_layout.itemAt(0).widget()
                if checkbox.isChecked():
                    selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select at least one course to delete!")
            return

        # Xác nhận xóa
        confirm = QMessageBox.question(self, "Confirm Deletion", 
                                      f"Are you sure you want to delete {len(selected_rows)} selected courses?",
                                      QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            # Xóa từ cuối lên để tránh lỗi index
            for row in sorted(selected_rows, reverse=True):
                if row < len(self.courses):
                    course_id = self.courses[row].id
                    self.course_controller.delete_course(course_id)

            # Cập nhật danh sách khóa học
            self.update_course_list()
            QMessageBox.information(self, "Success", f"{len(selected_rows)} courses have been deleted.")

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

            # Nếu đăng nhập thành công và có khóa học được chọn, điều hướng đến khóa học
            if success and self.selected_course:
                # Cập nhật URL của khóa học nếu cần
                if self.selected_course.url != url:
                    self.selected_course.url = url
                    self.course_controller.update_course(
                        self.selected_course.id, 
                        self.selected_course.name, 
                        url, 
                        self.selected_course.current_lesson
                    )

                # Nếu có URL bài học hiện tại, điều hướng đến đó
                if self.selected_course.current_lesson:
                    try:
                        # Điều hướng đến bài học hiện tại
                        driver = self.login_model.drivers.get(self.selected_username)
                        if driver:
                            print(f"Navigating to lesson: {self.selected_course.current_lesson}")
                            driver.get(self.selected_course.current_lesson)

                            # Tìm bài học tiếp theo (chưa hoàn thành)
                            self.find_next_incomplete_lesson(driver, self.selected_course)
                    except Exception as e:
                        print(f"Error navigating to lesson: {e}")

            # Nếu đăng nhập thất bại, đánh dấu user là đã dừng
            if not success:
                self.stop_user(user)

    def find_next_incomplete_lesson(self, driver, course):
        """
        Tìm và điều hướng đến bài học tiếp theo chưa hoàn thành

        Args:
            driver: WebDriver instance
            course: Course object
        """
        try:
            print("Searching for incomplete lessons...")

            # Đợi trang tải xong
            time.sleep(3)

            # Tìm tất cả các bài học
            lesson_elements = driver.find_elements(By.CSS_SELECTOR, ".lesson-item, .course-item, .slide-item")

            if not lesson_elements:
                print("No lesson elements found")
                return

            print(f"Found {len(lesson_elements)} lesson elements")

            # Tìm bài học chưa hoàn thành đầu tiên
            incomplete_lesson = None
            for element in lesson_elements:
                # Kiểm tra xem bài học đã hoàn thành chưa (thường có class hoặc icon đánh dấu)
                is_completed = "completed" in element.get_attribute("class") or "done" in element.get_attribute("class")

                if not is_completed:
                    incomplete_lesson = element
                    break

            if incomplete_lesson:
                print("Found incomplete lesson, clicking on it...")
                # Click vào bài học chưa hoàn thành
                incomplete_lesson.click()

                # Lưu URL của bài học vào course
                time.sleep(2)  # Đợi trang tải
                current_url = driver.current_url
                course.current_lesson = current_url

                # Cập nhật course trong database
                self.course_controller.update_course(
                    course.id, 
                    course.name, 
                    course.url, 
                    current_url
                )

                print(f"Updated current lesson to: {current_url}")
            else:
                print("No incomplete lessons found")

        except Exception as e:
            print(f"Error finding next incomplete lesson: {e}")

    def start_user(self, user):
        """Bắt đầu chạy một user (đánh dấu là đang chạy)"""
        user.status = "running"
        self.user_controller.update_user(user.id, user.username, user.password, user.url, user.hours, user.status, user.running_time)
        self.update_user_list()

    def stop_user(self, user):
        """Dừng chạy một user (đánh dấu là đã dừng)"""
        user.status = "stopped"
        self.user_controller.update_user(user.id, user.username, user.password, user.url, user.hours, user.status, user.running_time)
        # Đóng trình duyệt của user này nếu đang mở
        self.login_model.close_driver(user.username)
        self.update_user_list()

    def format_running_time(self, seconds):
        """Format thời gian chạy từ giây sang định dạng HH:MM:SS"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    def update_running_time(self):
        """Cập nhật thời gian chạy cho các user đang trong trạng thái running"""
        updated = False
        for user in self.users:
            if user.status == "running":
                user.running_time += 1
                self.user_controller.update_user(user.id, user.username, user.password, user.url, user.hours, user.status, user.running_time)
                updated = True

        if updated:
            self.update_user_list()

    def user_selected(self, item):
        """Xử lý khi người dùng chọn một dòng trong bảng"""
        row = item.row()
        if row >= 0 and row < len(self.users):
            user = self.users[row]
            self.selected_username = user.username
            self.selected_password = user.password
            self.url_input.setText(user.url)

            # Lưu user đang chọn
            self.selected_user = user

            # Cập nhật label hiển thị thông tin user đang chọn
            self.selected_user_label.setText(f"Selected user: {user.username}")

            # Cập nhật danh sách khóa học cho user đang chọn
            self.update_course_list()

    def course_selected(self, item):
        """Xử lý khi người dùng chọn một dòng trong bảng khóa học"""
        row = item.row()
        column = item.column()

        if row >= 0 and row < len(self.courses):
            course = self.courses[row]

            # Nếu người dùng click vào cột Completed, toggle trạng thái completed
            if column == 4:  # Completed column
                # Toggle completion status
                course.is_completed = 1 if course.is_completed == 0 else 0

                # Cập nhật course trong database
                self.course_controller.update_course(
                    course.id, 
                    course.name, 
                    course.url, 
                    course.current_lesson, 
                    course.completion_time,
                    course.is_completed
                )

                # Cập nhật lại danh sách khóa học
                self.update_course_list()

                # Cập nhật lại danh sách người dùng để hiển thị tỷ lệ hoàn thành mới
                self.update_user_list()

                return

            # Lưu course đang chọn
            self.selected_course = course

            # Cập nhật URL input để sử dụng URL của khóa học thay vì URL của user
            if course.url:
                self.url_input.setText(course.url)

    def save_course_checkbox_states(self):
        """Lưu trạng thái checkbox của các khóa học hiện tại vào dictionary"""
        for row in range(self.course_table.rowCount()):
            if row < len(self.courses):
                course = self.courses[row]
                checkbox_widget = self.course_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox_layout = checkbox_widget.layout()
                    checkbox = checkbox_layout.itemAt(0).widget()
                    self.course_checkbox_states[course.id] = checkbox.isChecked()

    def on_course_checkbox_changed(self, state, course_id):
        """Cập nhật trạng thái checkbox của khóa học trong dictionary khi checkbox thay đổi"""
        self.course_checkbox_states[course_id] = (state == Qt.Checked)

    def update_course_list(self):
        """Cập nhật danh sách khóa học trong table widget"""
        # Lưu trạng thái checkbox hiện tại trước khi cập nhật bảng
        self.save_course_checkbox_states()

        # Xóa bảng
        self.course_table.setRowCount(0)

        # Nếu không có user nào được chọn, không hiển thị khóa học
        if not self.selected_user:
            self.courses = []
            self.course_status_label.setText("Total courses: 0")
            return

        # Lấy danh sách khóa học cho user đang chọn
        self.courses = self.course_controller.get_courses_for_user(self.selected_user.id)

        # Cập nhật bảng với danh sách khóa học
        for row, course in enumerate(self.courses):
            self.course_table.insertRow(row)

            # Checkbox column
            checkbox = QCheckBox()
            # Khôi phục trạng thái checkbox từ dictionary
            is_checked = self.course_checkbox_states.get(course.id, False)
            checkbox.setChecked(is_checked)

            # Kết nối sự kiện stateChanged để cập nhật dictionary khi checkbox thay đổi
            checkbox.stateChanged.connect(lambda state, course_id=course.id: self.on_course_checkbox_changed(state, course_id))

            # Center the checkbox
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(checkbox)
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            # Make sure the widget is clickable
            cell_widget.setFocusPolicy(Qt.StrongFocus)
            self.course_table.setCellWidget(row, 0, cell_widget)

            # Name column
            name_item = QTableWidgetItem(course.name)
            self.course_table.setItem(row, 1, name_item)

            # URL column
            url_item = QTableWidgetItem(course.url)
            self.course_table.setItem(row, 2, url_item)

            # Current Lesson column
            lesson_item = QTableWidgetItem(course.current_lesson)
            self.course_table.setItem(row, 3, lesson_item)

            # Completed column
            completed_text = "Yes" if course.is_completed else "No"
            completed_item = QTableWidgetItem(completed_text)
            completed_item.setTextAlignment(Qt.AlignCenter)
            self.course_table.setItem(row, 4, completed_item)

            # Actions column
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            # Edit button
            edit_button = QToolButton()
            edit_button.setText("Edit")
            edit_button.setToolTip("Edit course")
            edit_button.clicked.connect(lambda checked, r=row: self.edit_course(r))

            # Delete button
            delete_button = QToolButton()
            delete_button.setText("Delete")
            delete_button.setToolTip("Delete course")
            delete_button.clicked.connect(lambda checked, r=row: self.delete_course(r))

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            self.course_table.setCellWidget(row, 5, actions_cell)

        # Cập nhật label hiển thị số lượng khóa học
        self.course_status_label.setText(f"Total courses: {len(self.courses)}")

    def filter_users(self, text):
        """Lọc danh sách người dùng theo từ khóa tìm kiếm"""
        if not text:
            # Nếu không có từ khóa, hiển thị tất cả
            self.update_user_list()
            return

        # Lưu trạng thái checkbox hiện tại trước khi cập nhật bảng
        self.save_checkbox_states()

        # Lọc danh sách người dùng theo từ khóa
        filtered_users = [user for user in self.users if 
                         text.lower() in user.username.lower() or 
                         text.lower() in user.url.lower()]

        # Cập nhật bảng với danh sách đã lọc
        self.user_table.setRowCount(0)
        for row, user in enumerate(filtered_users):
            self.user_table.insertRow(row)

            # Checkbox column - Direct checkbox for better click handling
            checkbox = QCheckBox()
            # Khôi phục trạng thái checkbox từ dictionary
            is_checked = self.checkbox_states.get(user.id, False)
            checkbox.setChecked(is_checked)

            # Kết nối sự kiện stateChanged để cập nhật dictionary khi checkbox thay đổi
            checkbox.stateChanged.connect(lambda state, user_id=user.id: self.on_checkbox_changed(state, user_id))

            # Center the checkbox
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(checkbox)
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            # Make sure the widget is clickable
            cell_widget.setFocusPolicy(Qt.StrongFocus)
            self.user_table.setCellWidget(row, 0, cell_widget)

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

            # Courses column (completion ratio)
            _, _, ratio_text = self.course_controller.get_completion_ratio(user.id)
            courses_item = QTableWidgetItem(ratio_text)
            courses_item.setTextAlignment(Qt.AlignCenter)
            self.user_table.setItem(row, 6, courses_item)

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
            self.user_table.setCellWidget(row, 7, actions_cell)

    def delete_selected_users(self):
        """Xóa tất cả người dùng đã chọn (đánh dấu checkbox)"""
        selected_rows = []
        for row in range(self.user_table.rowCount()):
            checkbox_widget = self.user_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_layout = checkbox_widget.layout()
                checkbox = checkbox_layout.itemAt(0).widget()
                if checkbox.isChecked():
                    selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select at least one user to delete!")
            return

        # Xác nhận xóa
        confirm = QMessageBox.question(self, "Confirm Deletion", 
                                      f"Are you sure you want to delete {len(selected_rows)} selected users?",
                                      QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            # Xóa từ cuối lên để tránh lỗi index
            for row in sorted(selected_rows, reverse=True):
                if row < len(self.users):
                    user_id = self.users[row].id
                    self.user_controller.delete_user(user_id)
                    del self.users[row]

            self.update_user_list()
            QMessageBox.information(self, "Success", f"{len(selected_rows)} users have been deleted.")

    def add_user(self):
        """Mở dialog thêm người dùng mới"""
        dialog = AddUserDialog(self)
        if dialog.exec_():
            # Get user data
            username, password, url, hours, course_url, completion_time = dialog.get_user_data()

            # Add user
            success, message, user_id = self.user_controller.add_user(username, password, url, hours)
            if success:
                # If course URL is provided, add a course for the user
                if course_url:
                    # Create a default course name based on the URL
                    course_name = "Course from " + course_url.split("//")[-1].split("/")[0]

                    # Add the course
                    course_success, course_message, _ = self.course_controller.add_course(
                        user_id, course_name, course_url, "", completion_time)

                    if not course_success:
                        QMessageBox.warning(self, "Warning", f"User added but failed to add course: {course_message}")

                # Lấy lại danh sách từ database
                self.users = self.user_controller.get_all_users()
                self.update_user_list()
                QMessageBox.information(self, "Success", "User added successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add user: {message}")

    def edit_user(self, row):
        """Mở dialog chỉnh sửa thông tin người dùng"""
        if row >= 0 and row < len(self.users):
            user = self.users[row]
            dialog = AddUserDialog(self, edit_mode=True, user=user)
            if dialog.exec_():
                # Get user data
                username, password, url, hours, course_url, completion_time = dialog.get_user_data()

                # Update user
                success, message = self.user_controller.update_user(user.id, username, password, url, hours, user.status, user.running_time)
                if success:
                    # Get existing courses for this user
                    courses = self.course_controller.get_courses_for_user(user.id)

                    if course_url:
                        if courses:
                            # Update the first course
                            course = courses[0]
                            course_success, course_message = self.course_controller.update_course(
                                course.id, course.name, course_url, course.current_lesson, completion_time)

                            if not course_success:
                                QMessageBox.warning(self, "Warning", f"User updated but failed to update course: {course_message}")
                        else:
                            # Create a default course name based on the URL
                            course_name = "Course from " + course_url.split("//")[-1].split("/")[0]

                            # Add a new course
                            course_success, course_message, _ = self.course_controller.add_course(
                                user.id, course_name, course_url, "", completion_time)

                            if not course_success:
                                QMessageBox.warning(self, "Warning", f"User updated but failed to add course: {course_message}")

                    # Lấy lại danh sách từ database
                    self.users = self.user_controller.get_all_users()
                    self.update_user_list()
                    QMessageBox.information(self, "Success", "User updated successfully!")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to update user: {message}")

    def delete_user(self, row):
        """Xóa một người dùng"""
        if row >= 0 and row < len(self.users):
            user = self.users[row]

            # Xác nhận xóa
            confirm = QMessageBox.question(self, "Confirm Deletion", 
                                          f"Are you sure you want to delete user '{user.username}'?",
                                          QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                success, message = self.user_controller.delete_user(user.id)
                if success:
                    del self.users[row]
                    self.update_user_list()
                    QMessageBox.information(self, "Success", "User deleted successfully!")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete user: {message}")

    def run_selected_users(self):
        """Chạy tất cả người dùng đã chọn (đánh dấu checkbox)"""
        selected_rows = []
        for row in range(self.user_table.rowCount()):
            checkbox_widget = self.user_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_layout = checkbox_widget.layout()
                checkbox = checkbox_layout.itemAt(0).widget()
                if checkbox.isChecked():
                    selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select at least one user to run!")
            return

        # Chạy từng user đã chọn
        for row in selected_rows:
            if row < len(self.users):
                user = self.users[row]
                # Đánh dấu user là đang chạy
                self.start_user(user)
                # Gọi login_controller để xử lý đăng nhập
                success = self.login_controller.handle_login(user.url, user.username, user.password)
                # Nếu đăng nhập thất bại, đánh dấu user là đã dừng
                if not success:
                    self.stop_user(user)

    def stop_all_users(self):
        """Dừng tất cả người dùng đang chạy trong danh sách"""
        running_users = [user for user in self.users if user.status == "running"]

        if not running_users:
            QMessageBox.information(self, "Information", "No users are currently running!")
            return

        # Xác nhận dừng tất cả
        confirm = QMessageBox.question(self, "Confirm Stop All", 
                                      f"Are you sure you want to stop all {len(running_users)} running users?",
                                      QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            # Dừng từng user đang chạy
            for user in running_users:
                self.stop_user(user)

            QMessageBox.information(self, "Success", f"Stopped {len(running_users)} users.")

    def stop_selected_users(self):
        """Dừng tất cả người dùng đã chọn (đánh dấu checkbox) và đang chạy"""
        selected_rows = []
        for row in range(self.user_table.rowCount()):
            checkbox_widget = self.user_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox_layout = checkbox_widget.layout()
                checkbox = checkbox_layout.itemAt(0).widget()
                if checkbox.isChecked():
                    selected_rows.append(row)

        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select at least one user to stop!")
            return

        # Lọc ra những user đang chạy
        running_users = []
        for row in selected_rows:
            if row < len(self.users):
                user = self.users[row]
                if user.status == "running":
                    running_users.append(user)

        if not running_users:
            QMessageBox.information(self, "Information", "None of the selected users are currently running!")
            return

        # Xác nhận dừng
        confirm = QMessageBox.question(self, "Confirm Stop Selected", 
                                      f"Are you sure you want to stop {len(running_users)} selected running users?",
                                      QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            # Dừng từng user đã chọn và đang chạy
            for user in running_users:
                self.stop_user(user)

            QMessageBox.information(self, "Success", f"Stopped {len(running_users)} users.")

    def run_all_users(self):
        """Chạy tất cả người dùng trong danh sách"""
        if not self.users:
            QMessageBox.warning(self, "Error", "No users available to run!")
            return

        # Xác nhận chạy tất cả
        confirm = QMessageBox.question(self, "Confirm Run All", 
                                      f"Are you sure you want to run all {len(self.users)} users?",
                                      QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            # Chạy từng user trong danh sách
            for user in self.users:
                # Đánh dấu user là đang chạy
                self.start_user(user)
                # Gọi login_controller để xử lý đăng nhập
                success = self.login_controller.handle_login(user.url, user.username, user.password)
                # Nếu đăng nhập thất bại, đánh dấu user là đã dừng
                if not success:
                    self.stop_user(user)

    def save_checkbox_states(self):
        """Lưu trạng thái checkbox hiện tại vào dictionary"""
        for row in range(self.user_table.rowCount()):
            if row < len(self.users):
                user = self.users[row]
                checkbox_widget = self.user_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox_layout = checkbox_widget.layout()
                    checkbox = checkbox_layout.itemAt(0).widget()
                    self.checkbox_states[user.id] = checkbox.isChecked()

    def on_checkbox_changed(self, state, user_id):
        """Cập nhật trạng thái checkbox trong dictionary khi checkbox thay đổi"""
        self.checkbox_states[user_id] = (state == Qt.Checked)

    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        # Đóng tất cả các trình duyệt đang mở
        self.login_model.close_all_drivers()
        # Chấp nhận sự kiện đóng
        event.accept()

# Chạy ứng dụng PyQt5
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
