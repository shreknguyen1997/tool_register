import pymysql
import os
from models.user_model import User
from models.course_model import Course

class DatabaseModel:
    def __init__(self, db_path=None):
        """
        Initialize the database connection and create tables if they don't exist

        Args:
            db_path (str, optional): Not used for MySQL, kept for backward compatibility
        """
        # MySQL connection parameters
        self.db_host = "127.0.0.1"
        self.db_port = 3306
        self.db_name = "register"
        self.db_user = "root"
        self.db_password = "root"

        self.connection = None
        self.cursor = None

        # Connect to database and create tables
        self.connect()

    def connect(self):
        """Connect to the MySQL database"""
        try:
            # First try to connect without specifying the database
            temp_connection = pymysql.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                cursorclass=pymysql.cursors.DictCursor
            )
            temp_cursor = temp_connection.cursor()

            # Check if the database exists
            temp_cursor.execute("SHOW DATABASES LIKE %s", (self.db_name,))
            database_exists = temp_cursor.fetchone()

            if not database_exists:
                print(f"Database '{self.db_name}' does not exist. Creating it...")
                temp_cursor.execute(f"CREATE DATABASE {self.db_name}")
                temp_connection.commit()
                print(f"Database '{self.db_name}' created successfully.")

            # Close the temporary connection
            temp_connection.close()

            # Now connect to the specific database
            self.connection = pymysql.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                cursorclass=pymysql.cursors.DictCursor  # This enables column access by name
            )
            self.cursor = self.connection.cursor()
        except pymysql.MySQLError as e:
            print(f"Error connecting to MySQL database: {e}")
            # Create a fallback in-memory database if MySQL connection fails
            self.connection = None
            self.cursor = None

    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()

    def create_tables(self):
        print("[DEVTOOLS] Creating tables...")
        """Create the necessary tables if they don't exist"""
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot create tables")
            return

        try:
            # Tạo bảng users
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                url VARCHAR(255) NOT NULL,
                hours INT DEFAULT 0,
                status VARCHAR(50) DEFAULT 'stopped',
                running_time INT DEFAULT 0
            )
            ''')

            # Tạo bảng user_urls để lưu trữ nhiều URL cho mỗi user
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_urls (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                url VARCHAR(255) NOT NULL,
                hours INT DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            ''')

            # Tạo bảng courses (khóa học)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                url VARCHAR(255) NOT NULL,
                current_lesson VARCHAR(255) DEFAULT '',
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completion_time INT DEFAULT 0,
                is_completed TINYINT DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            ''')

            self.connection.commit()

            # Add the user from the issue description if it doesn't exist
            username = "001097034799"
            password = "001097034799"
            primary_url = "https://hoclythuyetlaixe.eco-tek.com.vn/web/login"

            self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = self.cursor.fetchone()

            if not user:
                print(f"User '{username}' does not exist. Creating it...")
                self.cursor.execute("INSERT INTO users (username, password, url, hours) VALUES (%s, %s, %s, %s)",
                                  (username, password, primary_url, 1))
                self.connection.commit()
                print(f"User '{username}' created successfully.")

                # Get the user ID
                self.cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                user_id = self.cursor.fetchone()['id']

                # Add the course URL from the issue description
                course_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"

                # Check if the course already exists
                self.cursor.execute("SELECT * FROM courses WHERE user_id = %s AND url = %s", (user_id, course_url))
                course = self.cursor.fetchone()

                if not course:
                    print(f"Adding course for user '{username}'...")
                    self.cursor.execute("INSERT INTO courses (user_id, name, url, current_lesson) VALUES (%s, %s, %s, %s)",
                                      (user_id, "Cấu tạo và sửa chữa thông thường xe ô tô", course_url, ""))
                    self.connection.commit()
                    print(f"Course added for user '{username}'.")
            else:
                print(f"User '{username}' already exists.")

                # Update the user's password and URL if needed
                if user['password'] != password or user['url'] != primary_url:
                    self.cursor.execute("UPDATE users SET password = %s, url = %s WHERE username = %s",
                                      (password, primary_url, username))
                    self.connection.commit()
                    print(f"User '{username}' updated successfully.")

                # Get the user ID
                user_id = user['id']

                # Add the course URL from the issue description if it doesn't exist
                course_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"

                # Check if the course already exists
                self.cursor.execute("SELECT * FROM courses WHERE user_id = %s AND url = %s", (user_id, course_url))
                course = self.cursor.fetchone()

                if not course:
                    print(f"Adding course for user '{username}'...")
                    self.cursor.execute("INSERT INTO courses (user_id, name, url, current_lesson) VALUES (%s, %s, %s, %s)",
                                      (user_id, "Cấu tạo và sửa chữa thông thường xe ô tô", course_url, ""))
                    self.connection.commit()
                    print(f"Course added for user '{username}'.")
                else:
                    print(f"Course already exists for user '{username}'.")
        except pymysql.MySQLError as e:
            print(f"Error creating tables or adding data: {e}")
            self.connection.rollback()

    def get_all_users(self):
        """
        Get all users from the database

        Returns:
            list: List of User objects
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot get users")
            return []

        try:
            self.cursor.execute("SELECT * FROM users")
            rows = self.cursor.fetchall()

            users = []
            for row in rows:
                # Get additional URLs for this user
                user_id = row['id']
                urls = self.get_urls_for_user(user_id)

                user = User(
                    username=row['username'],
                    password=row['password'],
                    url=row['url'],
                    hours=row['hours'],
                    user_id=user_id,
                    status=row.get('status', 'stopped'),
                    running_time=row.get('running_time', 0),
                    urls=urls
                )
                users.append(user)

            return users
        except pymysql.MySQLError as e:
            print(f"Error getting users: {e}")
            return []

    def add_user(self, user):
        """
        Add a new user to the database

        Args:
            user (User): User object to add

        Returns:
            int: ID of the newly added user, or None if failed
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot add user")
            return None

        try:
            self.cursor.execute(
                "INSERT INTO users (username, password, url, hours, status, running_time) VALUES (%s, %s, %s, %s, %s, %s)",
                (user.username, user.password, user.url, user.hours, user.status, user.running_time)
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except pymysql.MySQLError as e:
            print(f"Error adding user: {e}")
            self.connection.rollback()
            return None

    def update_user(self, user_id, user):
        """
        Update an existing user in the database

        Args:
            user_id (int): ID of the user to update
            user (User): Updated User object

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot update user")
            return False

        try:
            self.cursor.execute(
                "UPDATE users SET username=%s, password=%s, url=%s, hours=%s, status=%s, running_time=%s WHERE id=%s",
                (user.username, user.password, user.url, user.hours, user.status, user.running_time, user_id)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Error updating user: {e}")
            self.connection.rollback()
            return False

    def delete_user(self, user_id):
        """
        Delete a user from the database

        Args:
            user_id (int): ID of the user to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot delete user")
            return False

        try:
            self.cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Error deleting user: {e}")
            self.connection.rollback()
            return False

    def search_users(self, search_term):
        """
        Search for users matching the search term

        Args:
            search_term (str): Term to search for in username, url

        Returns:
            list: List of matching User objects
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot search users")
            return []

        try:
            search_pattern = f"%{search_term}%"
            self.cursor.execute(
                "SELECT u.* FROM users u LEFT JOIN user_urls uu ON u.id = uu.user_id WHERE u.username LIKE %s OR u.url LIKE %s OR uu.url LIKE %s",
                (search_pattern, search_pattern, search_pattern)
            )
            rows = self.cursor.fetchall()

            users = []
            for row in rows:
                # Get additional URLs for this user
                user_id = row['id']
                urls = self.get_urls_for_user(user_id)

                user = User(
                    username=row['username'],
                    password=row['password'],
                    url=row['url'],
                    hours=row['hours'],
                    user_id=user_id,
                    status=row.get('status', 'stopped'),
                    running_time=row.get('running_time', 0),
                    urls=urls
                )
                users.append(user)

            return users
        except pymysql.MySQLError as e:
            print(f"Error searching users: {e}")
            return []

    # Course management methods
    def get_courses_for_user(self, user_id):
        """
        Get all courses for a specific user

        Args:
            user_id (int): ID of the user

        Returns:
            list: List of Course objects
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot get courses")
            return []

        try:
            self.cursor.execute("SELECT * FROM courses WHERE user_id = %s", (user_id,))
            rows = self.cursor.fetchall()

            courses = []
            for row in rows:
                course = Course(
                    user_id=row['user_id'],
                    name=row['name'],
                    url=row['url'],
                    current_lesson=row['current_lesson'],
                    last_accessed=row['last_accessed'],
                    course_id=row['id'],
                    completion_time=row.get('completion_time', 0),
                    is_completed=row.get('is_completed', 0)
                )
                courses.append(course)

            return courses
        except pymysql.MySQLError as e:
            print(f"Error getting courses: {e}")
            return []

    def add_course(self, course):
        """
        Add a new course to the database

        Args:
            course (Course): Course object to add

        Returns:
            int: ID of the newly added course, or None if failed
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot add course")
            return None

        try:
            self.cursor.execute(
                "INSERT INTO courses (user_id, name, url, current_lesson, completion_time, is_completed) VALUES (%s, %s, %s, %s, %s, %s)",
                (course.user_id, course.name, course.url, course.current_lesson, course.completion_time, course.is_completed)
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except pymysql.MySQLError as e:
            print(f"Error adding course: {e}")
            self.connection.rollback()
            return None

    def update_course(self, course_id, course):
        """
        Update an existing course in the database

        Args:
            course_id (int): ID of the course to update
            course (Course): Updated Course object

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot update course")
            return False

        try:
            self.cursor.execute(
                "UPDATE courses SET name=%s, url=%s, current_lesson=%s, completion_time=%s, is_completed=%s WHERE id=%s",
                (course.name, course.url, course.current_lesson, course.completion_time, course.is_completed, course_id)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Error updating course: {e}")
            self.connection.rollback()
            return False

    def delete_course(self, course_id):
        """
        Delete a course from the database

        Args:
            course_id (int): ID of the course to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot delete course")
            return False

        try:
            self.cursor.execute("DELETE FROM courses WHERE id=%s", (course_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Error deleting course: {e}")
            self.connection.rollback()
            return False

    # User URLs management methods
    def get_urls_for_user(self, user_id):
        """
        Get all URLs for a specific user

        Args:
            user_id (int): ID of the user

        Returns:
            list: List of dictionaries with 'url' and 'hours' keys
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot get URLs")
            return []

        try:
            self.cursor.execute("SELECT url, hours FROM user_urls WHERE user_id = %s", (user_id,))
            rows = self.cursor.fetchall()

            urls = [{'url': row['url'], 'hours': row['hours']} for row in rows]
            return urls
        except pymysql.MySQLError as e:
            print(f"Error getting URLs: {e}")
            return []

    def add_url_for_user(self, user_id, url, hours=0):
        """
        Add a new URL for a user

        Args:
            user_id (int): ID of the user
            url (str): URL to add
            hours (int): Number of hours for this URL (default: 0)

        Returns:
            int: ID of the newly added URL, or None if failed
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot add URL")
            return None

        try:
            self.cursor.execute(
                "INSERT INTO user_urls (user_id, url, hours) VALUES (%s, %s, %s)",
                (user_id, url, hours)
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except pymysql.MySQLError as e:
            print(f"Error adding URL: {e}")
            self.connection.rollback()
            return None

    def delete_url_for_user(self, url_id):
        """
        Delete a URL for a user

        Args:
            url_id (int): ID of the URL to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot delete URL")
            return False

        try:
            self.cursor.execute("DELETE FROM user_urls WHERE id=%s", (url_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Error deleting URL: {e}")
            self.connection.rollback()
            return False

    def delete_all_urls_for_user(self, user_id):
        """
        Delete all URLs for a user

        Args:
            user_id (int): ID of the user

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot delete URLs")
            return False

        try:
            self.cursor.execute("DELETE FROM user_urls WHERE user_id=%s", (user_id,))
            self.connection.commit()
            return True
        except pymysql.MySQLError as e:
            print(f"Error deleting URLs: {e}")
            self.connection.rollback()
            return False
