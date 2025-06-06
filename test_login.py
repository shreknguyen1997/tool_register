import sys
import os
from PyQt5.QtWidgets import QApplication
from models.login_model import LoginModel

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
    
    # Attempt to login
    print(f"Attempting to login with username: {username}, password: {password}, URL: {primary_url}")
    success = login_model.login(primary_url, username, password)
    
    if success:
        print("Login successful!")
        
        # Get the current URL after login
        driver = login_model.drivers.get(username)
        if driver:
            current_url = driver.current_url
            print(f"Current URL after login: {current_url}")
            
            # Check if we're still on the login page
            if "login" in current_url.lower():
                print("ERROR: Still on the login page after successful login!")
            else:
                print("SUCCESS: Redirected away from the login page after successful login.")
                
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