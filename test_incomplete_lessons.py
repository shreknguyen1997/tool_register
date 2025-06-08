import sys
import os
from PyQt5.QtWidgets import QApplication
from models.login_model import LoginModel
from models.database_model import DatabaseModel
from models.course_navigation_model import CourseNavigationModel
from models.course_model import Course
import time

def test_incomplete_lessons():
    """Test the functionality to find and navigate to lessons with less than 50% completion"""
    print("Testing functionality to find and navigate to lessons with less than 50% completion...")

    # Get the path to the ChromeDriver
    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(current_dir, "chromedriver", "chromedriver")
    print(f"ChromeDriver path: {driver_path}")

    # Create a database model
    db_model = DatabaseModel()

    # Create a login model
    login_model = LoginModel(driver_path)

    # Login credentials
    username = "001097034799"
    password = "001097034799"
    primary_url = "https://hoclythuyetlaixe.eco-tek.com.vn/web/login"
    course_url = "https://hoclythuyetlaixe.eco-tek.com.vn/slides/mon-hoc-phap-luat-giao-thong-uong-bo-2025-284"

    # Attempt to login
    print(f"Attempting to login with username: {username}, password: {password}, URL: {primary_url}")
    success = login_model.login(primary_url, username, password)

    if success:
        print("Login successful!")

        # Get the driver for this user
        driver = login_model.drivers.get(username)
        if driver:
            try:
                # Create a course navigation model
                course_nav_model = CourseNavigationModel(driver, db_model)

                # Find lessons with less than 50% completion
                print(f"Finding lessons with less than 50% completion in course: {course_url}")
                lessons_less_than_50_percent = course_nav_model.get_lessons_less_than_50_percent(course_url)

                if lessons_less_than_50_percent:
                    print(f"Found {len(lessons_less_than_50_percent)} lessons with less than 50% completion:")
                    
                    # Display the list of lessons with less than 50% completion
                    for i, lesson in enumerate(lessons_less_than_50_percent):
                        print(f"Lesson {i+1}: {lesson.get('title', 'No title')} - {lesson.get('url', 'No URL')} - {lesson.get('completion_percentage', 0)}%")
                    
                    # The get_lessons_less_than_50_percent method already clicks on the first lesson,
                    # so we just need to verify that we're on that lesson's page
                    current_url = driver.current_url
                    print(f"Current URL after finding lessons: {current_url}")
                    
                    # Check if we're on one of the lesson pages
                    on_lesson_page = False
                    for lesson in lessons_less_than_50_percent:
                        if lesson.get('url') in current_url:
                            print(f"SUCCESS: Navigated to lesson: {lesson.get('title', 'No title')}")
                            on_lesson_page = True
                            break
                    
                    if not on_lesson_page:
                        print(f"WARNING: Not on a lesson page. Current URL: {current_url}")
                        
                        # Try to navigate to the first lesson manually
                        if lessons_less_than_50_percent[0].get('url'):
                            first_lesson_url = lessons_less_than_50_percent[0].get('url')
                            print(f"Attempting to navigate to the first lesson: {first_lesson_url}")
                            driver.get(first_lesson_url)
                            time.sleep(3)  # Wait for the page to load
                            
                            current_url = driver.current_url
                            print(f"Current URL after manual navigation: {current_url}")
                            
                            if first_lesson_url in current_url:
                                print(f"SUCCESS: Manually navigated to the first lesson")
                            else:
                                print(f"ERROR: Failed to navigate to the first lesson")
                else:
                    print("No lessons with less than 50% completion found")

                # Wait for user input before closing
                input("Press Enter to close the browser and exit...")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("No driver found for this user")
    else:
        print("Login failed!")

    # Close all drivers
    login_model.close_all_drivers()

    return success

if __name__ == "__main__":
    # Create a QApplication instance (required for PyQt)
    app = QApplication(sys.argv)

    # Run the test
    success = test_incomplete_lessons()

    # Exit with appropriate code
    sys.exit(0 if success else 1)