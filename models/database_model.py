import pymysql
import os
from models.user_model import User

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
        self.create_tables()

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
        """Create the necessary tables if they don't exist"""
        if not self.connection or not self.cursor:
            print("Database connection not available, cannot create tables")
            return

        try:
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
            self.connection.commit()
        except pymysql.MySQLError as e:
            print(f"Error creating tables: {e}")
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
                user = User(
                    username=row['username'],
                    password=row['password'],
                    url=row['url'],
                    hours=row['hours'],
                    user_id=row['id'],
                    status=row.get('status', 'stopped'),
                    running_time=row.get('running_time', 0)
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
                "SELECT * FROM users WHERE username LIKE %s OR url LIKE %s",
                (search_pattern, search_pattern)
            )
            rows = self.cursor.fetchall()

            users = []
            for row in rows:
                user = User(
                    username=row['username'],
                    password=row['password'],
                    url=row['url'],
                    hours=row['hours'],
                    user_id=row['id'],
                    status=row.get('status', 'stopped'),
                    running_time=row.get('running_time', 0)
                )
                users.append(user)

            return users
        except pymysql.MySQLError as e:
            print(f"Error searching users: {e}")
            return []
