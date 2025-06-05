import sys
import os
from PyQt5.QtWidgets import QApplication
from app import MainWindow

def test_app():
    """Test the application's database connectivity and user management"""
    print("Testing application...")
    
    # Create the application
    app = QApplication(sys.argv)
    
    # Create the main window
    window = MainWindow()
    
    # Check if the database connection is working
    if window.db_model.connection and window.db_model.cursor:
        print("Database connection is working.")
    else:
        print("Database connection failed!")
        return False
    
    # Check if the user controller is working
    users = window.user_controller.get_all_users()
    print(f"Found {len(users)} users in the database.")
    
    # Test adding a user
    test_username = "test_user"
    test_password = "test_password"
    test_url = "https://example.com/test"
    test_hours = 3
    
    # Add the test user
    success, user_id, message = window.user_controller.add_user(
        test_username, test_password, test_url, test_hours
    )
    
    if success:
        print(f"Successfully added test user: {message}")
        
        # Get the updated user list
        users = window.user_controller.get_all_users()
        print(f"Now have {len(users)} users in the database.")
        
        # Find the test user
        test_user = None
        for user in users:
            if user.username == test_username:
                test_user = user
                break
        
        if test_user:
            print(f"Found test user with ID: {test_user.id}")
            
            # Test updating the user
            success, message = window.user_controller.update_user(
                test_user.id, test_username, test_password, test_url, test_hours + 1
            )
            
            if success:
                print(f"Successfully updated test user: {message}")
                
                # Test deleting the user
                success, message = window.user_controller.delete_user(test_user.id)
                
                if success:
                    print(f"Successfully deleted test user: {message}")
                    
                    # Verify the user was deleted
                    users = window.user_controller.get_all_users()
                    print(f"Now have {len(users)} users in the database.")
                    
                    # Check if the test user is gone
                    test_user_exists = any(user.username == test_username for user in users)
                    if not test_user_exists:
                        print("Test user was successfully deleted.")
                    else:
                        print("Error: Test user still exists after deletion!")
                        return False
                else:
                    print(f"Failed to delete test user: {message}")
                    return False
            else:
                print(f"Failed to update test user: {message}")
                return False
        else:
            print("Error: Could not find the test user after adding!")
            return False
    else:
        print(f"Failed to add test user: {message}")
        return False
    
    # Close the database connection
    window.user_controller.close_connection()
    print("Database connection closed.")
    
    print("All tests passed successfully!")
    return True

if __name__ == "__main__":
    success = test_app()
    sys.exit(0 if success else 1)