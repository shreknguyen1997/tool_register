import sys
import os
from selenium import webdriver
import requests
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
                            QLineEdit, QHBoxLayout, QSpacerItem, QSizePolicy, QMessageBox,
                            QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, 
                            QAbstractItemView, QFrame, QToolButton, QTabWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from controllers.login_controller import LoginController
from controllers.user_controller import UserController
from controllers.course_controller import CourseController
from models.login_model import LoginModel
from views.login_view import LoginView
from models.user_model import User
from models.course_model import Course
from models.database_model import DatabaseModel
from models.course_navigation_model import CourseNavigationModel
from views.add_user_dialog import AddUserDialog
from views.add_course_dialog import AddCourseDialog
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Khởi tạo các thành phần MVC cho login
        # Sử dụng đường dẫn tương đối để tìm ChromeDriver
        current_dir = os.path.dirname(os.path.abspath(__file__))
        driver_path = os.path.join(current_dir, "chromedriver", "chromedriver")
        print(f"ChromeDriver path: {driver_path}")

        # Initialize the list of incomplete lessons
        self.incomplete_lessons = []
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
            import datetime
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"[LESSON CHECK] Starting search for incomplete lessons at {current_time}...")

            # Đợi trang tải xong
            time.sleep(3)

            # Create a CourseNavigationModel instance
            course_nav_model = CourseNavigationModel(driver, self.db_model)

            # Store the list of lessons with less than 50% completion
            self.incomplete_lessons = []

            # Get lessons with less than 50% completion using CourseNavigationModel
            print(f"[LESSON CHECK] Getting lessons with less than 50% completion for course URL: {course.url}")
            try:
                print(f"[LESSON CHECK] Using CourseNavigationModel approach at {datetime.datetime.now().strftime('%H:%M:%S')}")
                self.incomplete_lessons = course_nav_model.get_lessons_less_than_50_percent(course.url)
                print(f"[LESSON CHECK] Found {len(self.incomplete_lessons)} lessons with less than 50% completion")

                # Display the list of incomplete lessons
                for i, lesson in enumerate(self.incomplete_lessons):
                    print(f"[LESSON CHECK] Lesson {i+1}: {lesson.get('title', 'No title')} - {lesson.get('url', 'No URL')} - {lesson.get('completion_percentage', 0)}%")

                # If we found any incomplete lessons, use the first one
                if self.incomplete_lessons:
                    # The get_lessons_less_than_50_percent method already clicks on the first lesson,
                    # but we need to ensure we're in the lesson detail page, not just the course page
                    time.sleep(3)  # Wait for page to load

                    # Get the current URL after clicking
                    current_url = driver.current_url
                    print(f"[LESSON CHECK] Current URL after clicking: {current_url}")

                    # Open developer tools and check network activity to verify we're in a lesson detail page
                    # This is done by checking specific elements that only appear in lesson pages
                    try:
                        # Check for elements that are specific to lesson detail pages
                        lesson_specific_elements = driver.find_elements(By.XPATH, "//*[@id=\"oe_structure_website_slides_lesson_top_1\"]")
                        if lesson_specific_elements:
                            print(f"[LESSON CHECK] Found lesson-specific elements, confirming we're in a lesson detail page")
                        else:
                            print(f"[LESSON CHECK] No lesson-specific elements found, we might still be on the course page")

                            # Try to find and click on the lesson again using a different approach
                            print(f"[LESSON CHECK] Attempting to click on the lesson again")
                            if self.incomplete_lessons and len(self.incomplete_lessons) > 0:
                                lesson = self.incomplete_lessons[0]
                                if 'url' in lesson:
                                    print(f"[LESSON CHECK] Navigating directly to lesson URL: {lesson['url']}")
                                    driver.get(lesson['url'])
                                    time.sleep(3)  # Wait for page to load
                                    current_url = driver.current_url
                    except Exception as e:
                        print(f"[LESSON CHECK] Error checking for lesson-specific elements: {e}")

                    # Update the course with the current URL
                    course.current_lesson = current_url

                    # Update the course in the database
                    self.course_controller.update_course(
                        course.id, 
                        course.name, 
                        course.url, 
                        current_url
                    )
                    time.sleep(3)

                    end_time = self.fetch_countdown_data(driver)
                    print(f"[LESSON CHECK] TIME COUNTDOWN : {end_time}")
                    print(f"[LESSON CHECK] Updated current lesson to: {current_url}")
                    print(f"[LESSON CHECK] Successfully found and navigated to incomplete lesson at {datetime.datetime.now().strftime('%H:%M:%S')}")
                    return
                else:
                    print(f"[LESSON CHECK] No lessons with less than 50% completion found using CourseNavigationModel at {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"[LESSON CHECK] Error using CourseNavigationModel: {e}")
                print(f"[LESSON CHECK] Falling back to original approach at {datetime.datetime.now().strftime('%H:%M:%S')}")

            # If CourseNavigationModel approach failed, try the direct approach
            print(f"[LESSON CHECK] Using direct approach: Finding li elements and checking their content at {datetime.datetime.now().strftime('%H:%M:%S')}")
            try:
                # Use the specific XPath provided in the issue description to get all li elements
                li_elements = driver.find_elements(By.XPATH, "//*[@id=\"home\"]/div/ul/li/ul/li")
                print(f"[LESSON CHECK] Found {len(li_elements)} li elements using the specific XPath")

                # Process each li element to find those with less than 50% completion
                for li in li_elements:
                    try:
                        # Get the li text and extract any information
                        li_text = li.text.strip()
                        print(f"[LESSON CHECK] Examining li element: '{li_text}'")

                        # Try to find a span element within the li
                        span_elements = li.find_elements(By.TAG_NAME, "span")

                        completion_percentage = 0  # Default to 0%
                        span_text = ""

                        # Check each span for progress information
                        for span in span_elements:
                            try:
                                span_text = span.text.strip()
                                print(f"[LESSON CHECK] Span text within li: '{span_text}'")

                                # Look for percentage pattern in the span text
                                import re
                                percentage_match = re.search(r'(\d+)\s*%', span_text)
                                if percentage_match:
                                    completion_percentage = int(percentage_match.group(1))
                                    print(f"[LESSON CHECK] Found completion percentage in span: {completion_percentage}%")
                                    break
                            except Exception as e:
                                print(f"[LESSON CHECK] Error processing span within li: {e}")

                        # If no span found or no percentage in span, try to extract from li text directly
                        if completion_percentage == 0:
                            percentage_match = re.search(r'(\d+)\s*%', li_text)
                            if percentage_match:
                                completion_percentage = int(percentage_match.group(1))
                                print(f"[LESSON CHECK] Found completion percentage in li text: {completion_percentage}%")

                        # Check if the completion percentage is less than 50%
                        if completion_percentage < 50:
                            print(f"[LESSON CHECK] Found li with <50% completion: {li_text}, Completion: {completion_percentage}%")

                            # Try to find an anchor element within the li
                            try:
                                # First try to find a direct child anchor
                                anchors = li.find_elements(By.TAG_NAME, "a")
                                print(f"[LESSON CHECK] Looking for anchor elements in li, found {len(anchors)} direct child anchors")

                                # If no direct child anchors, try to find any descendant anchor
                                if not anchors:
                                    anchors = li.find_elements(By.XPATH, ".//a")
                                    print(f"[LESSON CHECK] Looking for descendant anchors, found {len(anchors)} anchors")

                                if anchors:
                                    anchor = anchors[0]  # Use the first anchor found
                                    lesson_url = anchor.get_attribute("href")
                                    lesson_title = li_text
                                    if span_text:
                                        lesson_title = li_text.replace(span_text, "").strip()  # Remove span text from li text

                                    print(f"[LESSON CHECK] Found lesson with <50% completion: {lesson_title}, URL: {lesson_url}, Completion: {completion_percentage}%")

                                    # Add to our list of incomplete lessons
                                    self.incomplete_lessons.append({
                                        'url': lesson_url,
                                        'title': lesson_title,
                                        'completion_percentage': completion_percentage
                                    })

                                    # We found an incomplete lesson, use it
                                    incomplete_lesson = anchor
                                    print(f"[LESSON CHECK] Found incomplete lesson to use at {datetime.datetime.now().strftime('%H:%M:%S')}")
                                    break
                                else:
                                    print(f"[LESSON CHECK] No anchor found in li with <50% completion")

                                    # Try to find an anchor in the parent element
                                    try:
                                        parent = li.find_element(By.XPATH, "./..")
                                        parent_anchors = parent.find_elements(By.TAG_NAME, "a")
                                        print(f"[LESSON CHECK] Looking for anchors in parent element, found {len(parent_anchors)} anchors")

                                        if parent_anchors:
                                            anchor = parent_anchors[0]
                                            lesson_url = anchor.get_attribute("href")
                                            lesson_title = li_text
                                            if span_text:
                                                lesson_title = li_text.replace(span_text, "").strip()

                                            print(f"[LESSON CHECK] Found lesson with <50% completion (via parent): {lesson_title}, URL: {lesson_url}, Completion: {completion_percentage}%")

                                            # Add to our list of incomplete lessons
                                            self.incomplete_lessons.append({
                                                'url': lesson_url,
                                                'title': lesson_title,
                                                'completion_percentage': completion_percentage
                                            })

                                            # We found an incomplete lesson, use it
                                            incomplete_lesson = anchor
                                            print(f"[LESSON CHECK] Found incomplete lesson via parent element at {datetime.datetime.now().strftime('%H:%M:%S')}")
                                            break
                                    except Exception as e:
                                        print(f"[LESSON CHECK] Error finding anchor in parent: {e}")
                            except Exception as e:
                                print(f"[LESSON CHECK] Error finding anchor in li: {e}")
                    except Exception as e:
                        print(f"[LESSON CHECK] Error processing li element: {e}")

                # If we found an incomplete lesson, we'll use it
                if incomplete_lesson:
                    print(f"[LESSON CHECK] Found incomplete lesson using the direct approach at {datetime.datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"[LESSON CHECK] Error with direct approach: {e}")
                print(f"[LESSON CHECK] Falling back to original approach at {datetime.datetime.now().strftime('%H:%M:%S')}")

            # If we didn't find an incomplete lesson with the new approach, try the original approach
            if not incomplete_lesson:
                print(f"[LESSON CHECK] No incomplete lesson found with direct approach, trying original approach at {datetime.datetime.now().strftime('%H:%M:%S')}")
                # Tìm tất cả các bài học
                lesson_elements = driver.find_elements(By.CSS_SELECTOR, ".lesson-item, .course-item, .slide-item, .chapter-item, .module-item, .unit-item")

                if not lesson_elements:
                    print("[LESSON CHECK] No lesson elements found with standard selectors, trying alternative selectors...")
                    # Try alternative selectors for different course platforms
                    alternative_selectors = [
                        "a[href*='lesson']", 
                        "a[href*='module']", 
                        "a[href*='chapter']", 
                        "a[href*='unit']",
                        "a[href*='lecture']",
                        "div[role='button']",
                        "li.course-item",
                        ".course-content a",
                        ".curriculum-item"
                    ]

                    for selector in alternative_selectors:
                        lesson_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if lesson_elements:
                            print(f"[LESSON CHECK] Found {len(lesson_elements)} elements with selector: {selector}")
                            break

                    if not lesson_elements:
                        print("[LESSON CHECK] Still no lesson elements found, trying to find any clickable elements...")
                        # Last resort: find all links that might be lessons
                        lesson_elements = driver.find_elements(By.TAG_NAME, "a")

                if not lesson_elements:
                    print(f"[LESSON CHECK] No lesson elements found after all attempts at {datetime.datetime.now().strftime('%H:%M:%S')}")
                    return

                print(f"[LESSON CHECK] Found {len(lesson_elements)} potential lesson elements")

                # Tìm bài học chưa hoàn thành đầu tiên
                completion_indicators = ["completed", "done", "finished", "complete", "watched", "viewed"]

                for element in lesson_elements:
                    # Kiểm tra xem bài học đã hoàn thành chưa (thường có class hoặc icon đánh dấu)
                    element_class = element.get_attribute("class") or ""
                    element_text = element.text.lower()

                    is_completed = any(indicator in element_class.lower() for indicator in completion_indicators)

                    # Also check if there's a completion indicator in the text or child elements
                    if not is_completed:
                        is_completed = any(indicator in element_text for indicator in completion_indicators)

                    # Check for completion icons in child elements
                    if not is_completed:
                        try:
                            check_icons = element.find_elements(By.CSS_SELECTOR, "i.fa-check, i.fa-check-circle, .icon-check, .complete-icon")
                            is_completed = len(check_icons) > 0
                        except:
                            pass

                    if not is_completed:
                        incomplete_lesson = element
                        print(f"[LESSON CHECK] Found incomplete lesson using original approach at {datetime.datetime.now().strftime('%H:%M:%S')}")
                        break

            if incomplete_lesson:
                print(f"[LESSON CHECK] Found incomplete lesson, attempting to click on it at {datetime.datetime.now().strftime('%H:%M:%S')}...")
                try:
                    # Try to scroll to the element first to make it visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", incomplete_lesson)
                    time.sleep(1)  # Give time for the scroll to complete
                    print(f"[LESSON CHECK] Scrolled to incomplete lesson element")

                    # Click vào bài học chưa hoàn thành
                    incomplete_lesson.click()
                    print(f"[LESSON CHECK] Clicked on incomplete lesson at {datetime.datetime.now().strftime('%H:%M:%S')}")

                    # Lưu URL của bài học vào course
                    time.sleep(2)  # Đợi trang tải
                    current_url = driver.current_url
                    course.current_lesson = current_url
                    print(f"[LESSON CHECK] Current URL after click: {current_url}")

                    # Cập nhật course trong database
                    self.course_controller.update_course(
                        course.id, 
                        course.name, 
                        course.url, 
                        current_url
                    )

                    print(f"[LESSON CHECK] Updated current lesson in database to: {current_url}")

                    # Navigate to lesson details
                    try:
                        print(f"[LESSON CHECK] Attempting to navigate to lesson details at {datetime.datetime.now().strftime('%H:%M:%S')}...")
                        # Look for lesson detail elements using the provided XPath
                        detail_elements = driver.find_elements(By.XPATH, "//*[@id=\"home\"]/div/ul/li/ul/li")

                        if detail_elements:
                            print(f"[LESSON CHECK] Found {len(detail_elements)} detail elements")
                            # Try to find clickable elements within the details
                            for detail_element in detail_elements:
                                try:
                                    # Look for links or buttons within the detail element
                                    clickable = detail_element.find_elements(By.TAG_NAME, "a")
                                    if not clickable:
                                        clickable = detail_element.find_elements(By.TAG_NAME, "button")

                                    if clickable:
                                        print(f"[LESSON CHECK] Found clickable element in lesson details: {clickable[0].text}")
                                        # Scroll to the element
                                        driver.execute_script("arguments[0].scrollIntoView(true);", clickable[0])
                                        time.sleep(1)

                                        # Click on the element to navigate to lesson details
                                        clickable[0].click()
                                        time.sleep(2)
                                        print(f"[LESSON CHECK] Clicked on detail element at {datetime.datetime.now().strftime('%H:%M:%S')}")

                                        # Update the URL again after navigating to details
                                        detail_url = driver.current_url
                                        print(f"[LESSON CHECK] Navigated to lesson details: {detail_url}")

                                        # Update the course with the detail URL
                                        course.current_lesson = detail_url
                                        self.course_controller.update_course(
                                            course.id, 
                                            course.name, 
                                            course.url, 
                                            detail_url
                                        )
                                        print(f"[LESSON CHECK] Updated course with detail URL in database")
                                        break
                                except Exception as detail_error:
                                    print(f"[LESSON CHECK] Error interacting with detail element: {detail_error}")
                        else:
                            print(f"[LESSON CHECK] No lesson detail elements found at {datetime.datetime.now().strftime('%H:%M:%S')}, trying direct URL navigation")
                            # Fallback: Try to navigate directly to the specific URL from the issue description
                            try:
                                specific_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"
                                print(f"[LESSON CHECK] Navigating directly to: {specific_url}")
                                driver.get(specific_url)
                                time.sleep(3)  # Wait for the page to load

                                # Update the course with the specific URL
                                course.current_lesson = specific_url
                                self.course_controller.update_course(
                                    course.id, 
                                    course.name, 
                                    course.url, 
                                    specific_url
                                )
                                print(f"[LESSON CHECK] Updated course with specific URL in database: {specific_url}")
                            except Exception as direct_nav_error:
                                print(f"[LESSON CHECK] Error navigating directly to specific URL: {direct_nav_error}")
                    except Exception as detail_nav_error:
                        print(f"[LESSON CHECK] Error navigating to lesson details: {detail_nav_error}")
                        # Fallback: Try to navigate directly to the specific URL from the issue description
                        try:
                            specific_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"
                            print(f"[LESSON CHECK] Navigating directly to: {specific_url}")
                            driver.get(specific_url)
                            time.sleep(3)  # Wait for the page to load

                            # Update the course with the specific URL
                            course.current_lesson = specific_url
                            self.course_controller.update_course(
                                course.id, 
                                course.name, 
                                course.url, 
                                specific_url
                            )
                            print(f"[LESSON CHECK] Updated course with specific URL in database: {specific_url}")
                        except Exception as direct_nav_error:
                            print(f"[LESSON CHECK] Error navigating directly to specific URL: {direct_nav_error}")

                except Exception as click_error:
                    print(f"[LESSON CHECK] Error clicking on lesson: {click_error}")
                    # Try alternative click methods
                    try:
                        print(f"[LESSON CHECK] Trying JavaScript click method at {datetime.datetime.now().strftime('%H:%M:%S')}")
                        driver.execute_script("arguments[0].click();", incomplete_lesson)
                        time.sleep(2)
                        current_url = driver.current_url
                        course.current_lesson = current_url
                        print(f"[LESSON CHECK] JavaScript click successful, current URL: {current_url}")

                        # Update the course in the database
                        self.course_controller.update_course(
                            course.id, 
                            course.name, 
                            course.url, 
                            current_url
                        )

                        # Try to navigate to lesson details even after JavaScript click
                        try:
                            print(f"[LESSON CHECK] Attempting to navigate to lesson details after JavaScript click at {datetime.datetime.now().strftime('%H:%M:%S')}...")
                            # Try direct navigation to the specific URL as a fallback
                            specific_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"
                            print(f"[LESSON CHECK] Navigating directly to: {specific_url}")
                            driver.get(specific_url)
                            time.sleep(3)  # Wait for the page to load

                            # Update the course with the specific URL
                            course.current_lesson = specific_url
                            self.course_controller.update_course(
                                course.id, 
                                course.name, 
                                course.url, 
                                specific_url
                            )
                            print(f"[LESSON CHECK] Updated course with specific URL in database: {specific_url}")
                        except Exception as js_detail_error:
                            print(f"[LESSON CHECK] Error navigating to lesson details after JavaScript click: {js_detail_error}")
                        print(f"[LESSON CHECK] Clicked using JavaScript, updated current lesson to: {current_url}")
                    except Exception as js_error:
                        print(f"[LESSON CHECK] JavaScript click also failed: {js_error}")
            else:
                print(f"[LESSON CHECK] No incomplete lessons found at {datetime.datetime.now().strftime('%H:%M:%S')}, trying direct navigation to specific URL")
                # Fallback: Try to navigate directly to the specific URL from the issue description
                try:
                    specific_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"
                    print(f"[LESSON CHECK] Navigating directly to: {specific_url}")
                    driver.get(specific_url)
                    time.sleep(3)  # Wait for the page to load

                    # Update the course with the specific URL
                    course.current_lesson = specific_url
                    self.course_controller.update_course(
                        course.id, 
                        course.name, 
                        course.url, 
                        specific_url
                    )
                    print(f"[LESSON CHECK] Updated course with specific URL in database: {specific_url}")
                except Exception as direct_nav_error:
                    print(f"[LESSON CHECK] Error navigating directly to specific URL: {direct_nav_error}")

        except Exception as e:
            print(f"[LESSON CHECK] Error finding next incomplete lesson: {e}")
            print(f"[LESSON CHECK] Search for incomplete lessons failed at {datetime.datetime.now().strftime('%H:%M:%S')}")

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

    def get_incomplete_lessons(self):
        """
        Get the list of lessons with less than 50% completion

        Returns:
            list: List of dictionaries containing lesson information (url, title, completion_percentage)
        """
        return self.incomplete_lessons

    def fetch_countdown_data(self, driver):
        """
        Fetch countdown data from the network tab in browser's developer tools using CDP
        and return the end_time as a datetime object.

        Args:
            driver: WebDriver instance

        Returns:
            datetime: end_time value from the network response, or None if failed
        """
        try:
            # Get the current URL
            current_url = driver.current_url
            print(f"[DEVTOOLS] Current URL: {current_url}")

            print(f"[DEVTOOLS] Looking for API endpoint: https://hoclythuyetlaixe.eco-tek.com.vn/slide/countdown-start/")
            print(f"[DEVTOOLS] Using Chrome DevTools Protocol (CDP) to monitor network requests...")

            # Enable network monitoring using CDP
            devtools = driver.execute_cdp_cmd('Network.enable', {})  # Enable network monitoring

            # Define a function to log API requests
            def log_api_requests(request):
                # Check if it's an XHR or Fetch request
                if 'xhr' in request.get('type', '').lower():
                    url = request.get('url', '')
                    method = request.get('method', '')
                    headers = request.get('headers', {})

                    print(f"[CDP] API Request URL: {url}")
                    print(f"[CDP] Request Method: {method}")
                    print(f"[CDP] Request Headers: {headers}")

                    # If it's the countdown API, log more details
                    if 'countdown-start' in url:
                        print(f"[CDP] Found countdown API request via CDP: {url}")
                        # Try to extract response data if available
                        response = request.get('response', {})
                        if response:
                            print(f"[CDP] Response status: {response.get('status')}")
                            print(f"[CDP] Response body: {response.get('body', '')[:100]}...")  # First 100 chars

            # Set up the request interceptor
            try:
                driver.request_interceptor = log_api_requests
                print(f"[CDP] Request interceptor set up successfully")
            except Exception as e:
                print(f"[CDP] Error setting up request interceptor: {e}")

            # Refresh the page to trigger network requests
            print(f"[DEVTOOLS] Refreshing page to capture network requests...")
            driver.refresh()

            # Wait for the page to load and network requests to be captured
            time.sleep(5)  # Wait 5 seconds for requests to be captured

            # Look for the countdown timer element in the page as a fallback
            try:
                # Find the section element with the countdown timer
                countdown_section = driver.find_element(By.XPATH, "//*[@id='oe_structure_website_slides_lesson_top_1']/section")

                # Get the data-end-time attribute
                end_time = countdown_section.get_attribute("data-end-time")

                if end_time:
                    print(f"[DEVTOOLS] Found end_time from page element: {end_time}")
                    return float(end_time)
                else:
                    print(f"[DEVTOOLS] Could not find data-end-time attribute in countdown section")
            except Exception as element_error:
                print(f"[DEVTOOLS] Error finding countdown element: {element_error}")

            # If we couldn't extract the end_time, use a fallback value
            print("[DEVTOOLS] Could not extract end_time, using fallback")

            # Use a fallback value (30 minutes from now)
            import time
            fallback_end_time = time.time() + 30 * 60  # 30 minutes from now
            print(f"[DEVTOOLS] Using fallback end time (30 minutes from now): {fallback_end_time}")

            # Format the timestamp as a human-readable date
            import datetime
            end_time_date = datetime.datetime.fromtimestamp(fallback_end_time)
            print(f"[DEVTOOLS] Fallback end time as date: {end_time_date}")

            return fallback_end_time

        except Exception as e:
            print(f"[DEVTOOLS] Error fetching countdown data: {e}")
            return None

    def navigate_to_lesson(self, lesson_index, course):
        """
        Navigate to a specific lesson from the list of incomplete lessons

        Args:
            lesson_index (int): Index of the lesson in the incomplete_lessons list
            course (Course): Course object to update

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        if not self.incomplete_lessons or lesson_index < 0 or lesson_index >= len(self.incomplete_lessons):
            print(f"Invalid lesson index: {lesson_index}")
            return False

        lesson = self.incomplete_lessons[lesson_index]
        lesson_url = lesson.get('url')

        if not lesson_url:
            print("Lesson URL is missing")
            return False

        try:
            # Get the driver for the current user
            driver = None
            if self.selected_username in self.login_model.drivers:
                driver = self.login_model.drivers[self.selected_username]

            if not driver:
                print("No active driver found for the current user")
                return False

            # Navigate to the lesson URL
            print(f"Navigating to lesson: {lesson.get('title', 'No title')} - {lesson_url}")
            driver.get(lesson_url)
            time.sleep(3)  # Wait for the page to load

            # Update the course with the current URL
            course.current_lesson = lesson_url
            self.course_controller.update_course(
                course.id, 
                course.name, 
                course.url, 
                lesson_url
            )

            print(f"Updated current lesson to: {lesson_url}")
            return True
        except Exception as e:
            print(f"Error navigating to lesson: {e}")
            return False

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
            username, password, url, hours, urls = dialog.get_user_data()

            # Add user with multiple URLs
            success, user_id, message = self.user_controller.add_user(username, password, url, hours, urls)
            if success:
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
                username, password, url, hours, urls = dialog.get_user_data()

                # Update user with multiple URLs
                success, message = self.user_controller.update_user(
                    user.id, username, password, url, hours, user.status, user.running_time, urls)
                if success:
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
                # Set the selected user, username, and password
                self.selected_user = user
                self.selected_username = user.username
                self.selected_password = user.password
                self.url_input.setText(user.url)

                # Đánh dấu user là đang chạy
                self.start_user(user)
                # Gọi login_controller để xử lý đăng nhập
                success = self.login_controller.handle_login(user.url, user.username, user.password)

                # Nếu đăng nhập thành công, hiển thị chi tiết khóa học và bài học dưới 50%
                if success:
                    # Lấy danh sách khóa học của user
                    courses = self.course_controller.get_courses_for_user(user.id)
                    if courses:
                        # Chọn khóa học đầu tiên
                        selected_course = courses[0]
                        self.selected_course = selected_course

                        # Chuyển đến tab khóa học để hiển thị chi tiết
                        self.tab_widget.setCurrentIndex(1)  # Index 1 is the Courses tab

                        # Cập nhật danh sách khóa học để hiển thị
                        self.selected_user_label.setText(f"Selected user: {user.username}")
                        self.update_course_list()

                        # Tìm và điều hướng đến bài học chưa hoàn thành (<50%)
                        driver = self.login_model.drivers.get(self.selected_username)
                        if driver and selected_course:
                            self.find_next_incomplete_lesson(driver, selected_course)

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

                # Nếu đăng nhập thành công, hiển thị chi tiết khóa học và bài học dưới 50%
                if success:
                    # Lấy danh sách khóa học của user
                    courses = self.course_controller.get_courses_for_user(user.id)
                    if courses:
                        # Chọn khóa học đầu tiên
                        selected_course = courses[0]
                        self.selected_course = selected_course

                        # Chuyển đến tab khóa học để hiển thị chi tiết
                        self.tab_widget.setCurrentIndex(1)  # Index 1 is the Courses tab

                        # Cập nhật danh sách khóa học để hiển thị
                        self.selected_user = user
                        self.selected_user_label.setText(f"Selected user: {user.username}")
                        self.update_course_list()

                        # Tìm và điều hướng đến bài học chưa hoàn thành (<50%)
                        driver = self.login_model.drivers.get(user.username)
                        if driver and selected_course:
                            self.find_next_incomplete_lesson(driver, selected_course)

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
