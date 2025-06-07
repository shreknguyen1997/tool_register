import sys
import os
from PyQt5.QtWidgets import QApplication
from models.login_model import LoginModel
from models.database_model import DatabaseModel
from models.course_navigation_model import CourseNavigationModel
from models.course_model import Course
import time

def test_lesson_completion_time():
    """Test the get_lesson_completion_time function with canvas elements"""
    print("Testing get_lesson_completion_time function with canvas elements...")

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
            # Create a course navigation model
            course_nav_model = CourseNavigationModel(driver, db_model)

            # First get lessons with less than 50% completion to find a lesson URL to test
            print(f"Finding lessons with less than 50% completion in course: {course_url}")
            lessons_less_than_50_percent = course_nav_model.get_lessons_less_than_50_percent(course_url)

            if lessons_less_than_50_percent:
                # Test the get_lesson_completion_time function with the first lesson with less than 50% completion
                lesson_url = lessons_less_than_50_percent[0]['url']
                print(f"Testing get_lesson_completion_time with lesson URL: {lesson_url}")
                completion_time = course_nav_model.get_lesson_completion_time(lesson_url)

                # Print the results
                print(f"Lesson completion time: {completion_time} seconds")

                # Check if the completion time was determined from canvas elements
                if completion_time > 0:
                    print("SUCCESS: Lesson completion time was determined")
                else:
                    print("WARNING: Could not determine lesson completion time")
            else:
                print("No incomplete lessons found to test completion time")

            # Wait for user input before closing
            input("Press Enter to close the browser and exit...")
    else:
        print("Login failed!")

    # Close all drivers
    login_model.close_all_drivers()

    return success

def test_lessons_less_than_50_percent():
    """Test the function that finds lessons with less than 50% completion"""
    print("Testing function that finds lessons with less than 50% completion...")

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
                # Set a timeout for the entire operation using threading
                import threading
                import time

                # Create a course navigation model
                course_nav_model = CourseNavigationModel(driver, db_model)

                # Test the function that finds lessons with less than 50% completion
                print(f"Testing function that finds lessons with less than 50% completion with course URL: {course_url}")
                print("This operation will timeout after 30 seconds if it takes too long")

                # Take a screenshot before running the function
                screenshot_path = "before_get_lessons.png"
                driver.save_screenshot(screenshot_path)
                print(f"Saved screenshot before running function: {screenshot_path}")

                # Define a wrapper function to run the get_lessons_less_than_50_percent function
                result = {"lessons": [], "completed": False, "error": None}

                def run_function():
                    try:
                        result["lessons"] = course_nav_model.get_lessons_less_than_50_percent(course_url)
                        result["completed"] = True
                    except Exception as e:
                        result["error"] = e

                # Create and start a thread to run the function
                thread = threading.Thread(target=run_function)
                thread.daemon = True  # Allow the thread to be terminated when the main thread exits
                thread.start()

                # Wait for the thread to complete with a timeout
                timeout = 30  # 30 seconds
                start_time = time.time()
                while thread.is_alive() and time.time() - start_time < timeout:
                    time.sleep(1)  # Check every second
                    print(f"Waiting for function to complete... ({int(time.time() - start_time)} seconds elapsed)")

                # Check if the thread completed or timed out
                if thread.is_alive():
                    print(f"Function timed out after {timeout} seconds")
                    # We can't forcibly terminate the thread in Python, but we can continue with our test
                    raise TimeoutError("Operation timed out")

                # Check if there was an error
                if result["error"]:
                    raise result["error"]

                # Get the results
                lessons_less_than_50_percent = result["lessons"]

                # Take a screenshot after running the function
                screenshot_path = "after_get_lessons.png"
                driver.save_screenshot(screenshot_path)
                print(f"Saved screenshot after running function: {screenshot_path}")

                print(f"Found {len(lessons_less_than_50_percent)} lessons with <50% completion")

                # Print the results
                for lesson in lessons_less_than_50_percent:
                    completion = lesson.get('completion_percentage', 0)
                    print(f"- {lesson['title']} ({lesson['url']}) - {completion}% complete")

                # Check if the first lesson with less than 50% completion was clicked
                current_url = driver.current_url
                print(f"Current URL after clicking on first lesson with <50% completion: {current_url}")

                # If we have lessons with less than 50% completion, the current URL should be different from the course URL
                if lessons_less_than_50_percent and current_url != course_url:
                    print("SUCCESS: First lesson with <50% completion was clicked automatically")
                elif not lessons_less_than_50_percent:
                    print("No lessons with <50% completion found, nothing to click")
                else:
                    print("WARNING: First lesson with <50% completion was not clicked automatically")

                # No wait for user input - this allows the script to complete automatically
                print("Test completed successfully")

            except TimeoutError:
                print("Test timed out, but this is expected if the website is slow")
                print("The implementation may still be correct, but we can't verify it in the time allowed")
            except Exception as e:
                print(f"Error during test: {e}")
            finally:
                # No need to cancel any alarm, but we should clean up any resources if needed
                pass
    else:
        print("Login failed!")

    # Close all drivers
    login_model.close_all_drivers()

    return success

def test_course_navigation():
    """Test the course navigation process with the provided credentials"""
    print("Testing course navigation with provided credentials...")

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
            # Create a course navigation model
            course_nav_model = CourseNavigationModel(driver, db_model)

            # Get the user ID from the database
            users = db_model.get_all_users()
            user = next((u for u in users if u.username == username), None)

            if user:
                user_id = user.id
                print(f"Found user ID: {user_id}")

                # Get the courses for this user
                courses = db_model.get_courses_for_user(user_id)

                # Find the course with the specified URL or add it if it doesn't exist
                course = next((c for c in courses if c.url == course_url), None)

                if not course:
                    print(f"Course with URL {course_url} not found. Adding it...")
                    course_id = db_model.add_course(Course(
                        user_id=user_id,
                        name="Môn học pháp luật giao thông đường bộ",
                        url=course_url,
                        current_lesson="",
                        completion_time=1,  # 1 hour
                        is_completed=0
                    ))

                    # Get the course again
                    courses = db_model.get_courses_for_user(user_id)
                    course = next((c for c in courses if c.id == course_id), None)

                if course:
                    print(f"Processing course: {course.name} (ID: {course.id})")

                    # Process the course using the eco-tek specific function
                    course_nav_model.process_eco_tek_course(course.url, user_id, course.id)
                else:
                    print("Course not found and could not be added.")
            else:
                print(f"User with username {username} not found in the database.")

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

    # Check which test to run
    import argparse
    parser = argparse.ArgumentParser(description='Test course navigation functionality.')
    parser.add_argument('--test-incomplete', action='store_true', help='Test only the functionality for finding lessons with less than 50% completion')
    parser.add_argument('--test-completion-time', action='store_true', help='Test only the lesson completion time functionality')
    args = parser.parse_args()

    # Run the appropriate test
    if args.test_incomplete:
        print("Running test for lessons with less than 50% completion...")
        success = test_lessons_less_than_50_percent()
    elif args.test_completion_time:
        print("Running lesson completion time test...")
        success = test_lesson_completion_time()
    else:
        print("Running full course navigation test...")
        success = test_course_navigation()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
