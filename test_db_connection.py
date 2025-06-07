import pymysql
import sys

def test_mysql_connection():
    """Test the connection to the MySQL database"""
    print("Testing MySQL connection...")

    # MySQL connection parameters
    db_host = "127.0.0.1"
    db_port = 3306
    db_name = "register"
    db_user = "root"
    db_password = ""

    try:
        # First try to connect without specifying the database
        print("Connecting to MySQL server...")
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()

        # Check if the database exists
        cursor.execute("SHOW DATABASES LIKE %s", (db_name,))
        database_exists = cursor.fetchone()

        if not database_exists:
            print(f"Database '{db_name}' does not exist. Creating it...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully.")

        # Select the database
        cursor.execute(f"USE {db_name}")
        print(f"Using database '{db_name}'")

        # Check if the users table exists
        cursor.execute("SHOW TABLES LIKE 'users'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("Table 'users' does not exist. Creating it...")
            cursor.execute('''
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                url VARCHAR(255) NOT NULL,
                hours INT DEFAULT 0,
                status VARCHAR(50) DEFAULT 'stopped',
                running_time INT DEFAULT 0
            )
            ''')
            print("Table 'users' created successfully.")
        else:
            # Check if status column exists
            cursor.execute("SHOW COLUMNS FROM users LIKE 'status'")
            status_exists = cursor.fetchone()
            if not status_exists:
                print("Adding 'status' column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN status VARCHAR(50) DEFAULT 'stopped'")
                print("Added 'status' column successfully.")

            # Check if running_time column exists
            cursor.execute("SHOW COLUMNS FROM users LIKE 'running_time'")
            running_time_exists = cursor.fetchone()
            if not running_time_exists:
                print("Adding 'running_time' column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN running_time INT DEFAULT 0")
                print("Added 'running_time' column successfully.")

        # Create a cursor
        cursor = connection.cursor()

        # Test a simple query
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print("Connection successful!")
        print(f"Tables in database '{db_name}':")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"- {table_name}")

            # Show table structure
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  - {column['Field']} ({column['Type']})")

        # Check if the user with the specified credentials exists
        username = "001097034799"
        password = "001097034799"
        primary_url = "https://hoclythuyetlaixe.eco-tek.com.vn/web/login"

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            print(f"User '{username}' already exists. Updating password and URL...")
            cursor.execute("UPDATE users SET password = %s, url = %s WHERE username = %s", 
                          (password, primary_url, username))
            connection.commit()
            print(f"User '{username}' updated successfully.")
        else:
            print(f"User '{username}' does not exist. Creating it...")
            cursor.execute("INSERT INTO users (username, password, url, hours) VALUES (%s, %s, %s, %s)", 
                          (username, password, primary_url, 1))
            connection.commit()
            print(f"User '{username}' created successfully.")

            # Get the user ID
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_id = cursor.fetchone()['id']

            # Add a course for the user
            course_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"
            cursor.execute("INSERT INTO courses (user_id, name, url, current_lesson) VALUES (%s, %s, %s, %s)", 
                          (user_id, "Cấu tạo và sửa chữa thông thường xe ô tô", course_url, ""))
            connection.commit()
            print(f"Course added for user '{username}'.")

        # Close the connection
        connection.close()
        print("Connection closed.")
        return True

    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL database: {e}")
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)
