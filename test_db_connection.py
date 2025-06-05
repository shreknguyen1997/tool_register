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
                hours INT DEFAULT 0
            )
            ''')
            print("Table 'users' created successfully.")

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
