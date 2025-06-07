import sys
import os
from PyQt5.QtWidgets import QApplication
from models.login_model import LoginModel
import time

def test_login():
    """Test the login process with the provided credentials"""
    print("Testing login with provided credentials...")

    # Get the path to the ChromeDriver
    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(current_dir, "chromedriver", "chromedriver")
    print(f"ChromeDriver path: {driver_path}")

    # Create a login model
    login_model = LoginModel(driver_path)

    # Login credentials from the issue description
    username = "001097034799"
    password = "001097034799"
    primary_url = "https://hoclythuyetlaixe.eco-tek.com.vn/web/login"
    course_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283"

    # Attempt to login
    print(f"Attempting to login with username: {username}, password: {password}, URL: {primary_url}")
    success = login_model.login(primary_url, username, password)

    if success:
        print("Login successful!")

        # Get the current URL after login
        driver = login_model.drivers.get(username)
        if driver:
            current_url = driver.current_url
            print(f"Current URL after login and redirection: {current_url}")

            # Check if we're on the course page
            if course_url in current_url:
                print(f"SUCCESS: Redirected to the course page: {course_url}")
            else:
                print(f"WARNING: Not on the expected course page. Current URL: {current_url}")

                # Try to navigate to the course URL manually
                try:
                    print(f"Attempting to navigate to the course URL: {course_url}")
                    driver.get(course_url)
                    time.sleep(5)  # Wait for the page to load
                    print(f"Current URL after manual navigation: {driver.current_url}")

                    if course_url in driver.current_url:
                        print(f"SUCCESS: Successfully navigated to the course page: {course_url}")
                    else:
                        print(f"ERROR: Failed to navigate to the course page. Current URL: {driver.current_url}")
                except Exception as e:
                    print(f"ERROR: Exception when trying to navigate to the course URL: {e}")

            # Wait for user input before closing
            input("Press Enter to close the browser and exit...")
    else:
        print("Login failed!")

    # Close all drivers
    login_model.close_all_drivers()

    return success

if __name__ == "__main__":
    # Create a QApplication instance (required for PyQt)
    app = QApplication(sys.argv)

    # Run the test
    success = test_login()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
