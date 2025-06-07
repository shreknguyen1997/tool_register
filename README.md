# Login and Course Access Tool

This tool automates the login process for a driving theory learning website, navigates to specific course pages, and manages course progression.

## Changes Made

1. **Database Model (database_model.py)**:
   - Updated to ensure the database is properly set up with the necessary tables (users, user_urls, courses)
   - Added code to automatically create the user with the provided credentials if it doesn't exist
   - Added code to automatically add the course URL for the user if it doesn't exist

2. **Login Model (login_model.py)**:
   - Improved login success detection to better handle different login page designs
   - Added automatic redirection to the course URL after successful login
   - Added error handling for the redirection process

3. **Test Login Script (test_login.py)**:
   - Enhanced to provide better feedback about the login and redirection process
   - Added fallback mechanism to manually navigate to the course URL if automatic redirection doesn't work

4. **Course Navigation Model (course_navigation_model.py)**:
   - Created a new model to handle course navigation and progression
   - Implemented the `get_lessons_less_than_50_percent` function to find lessons with less than 50% completion using the specific XPath `//*[@id="home"]/div/ul/li/ul/li`
   - Enhanced lesson detection to extract and check completion percentages from various indicators
   - Added functionality to automatically click on the first lesson with less than 50% completion to start learning
   - Added functionality to determine lesson completion time by checking canvas elements
   - Implemented automatic navigation to the next lesson using the specific XPath `//*[@id="next-slide-button"]`
   - Added course completion tracking based on user settings
   - Implemented automatic progression to the next course when the current one is completed
   - Created specialized functions for different learning center platforms (starting with eco-tek.com.vn)

5. **Test Course Navigation Script (test_course_navigation.py)**:
   - Created a new test script to verify course navigation functionality
   - Tests finding incomplete lessons, lesson completion, and course progression

6. **Main Application (app.py)**:
   - Updated the `find_next_incomplete_lesson` method to use the specific XPath `//*[@id="home"]/div/ul/li/ul/li`
   - Enhanced lesson detection to extract and check completion percentages from span elements
   - Added functionality to find and click on lessons with less than 50% completion
   - Improved lesson detail access by using a more targeted approach to find lesson elements
   - Kept the original approach as a fallback for compatibility with different course platforms

## Testing Instructions

### Testing Login Functionality

1. Make sure you have a MySQL server running on localhost (127.0.0.1) with:
   - Username: root
   - Password: (empty)
   - If your MySQL configuration is different, update the connection parameters in database_model.py

2. Run the database connection test to ensure the database is properly set up:
   ```
   python test_db_connection.py
   ```
   This will create the necessary database, tables, and add the user and course information if they don't exist.

3. Run the login test to verify that the login process works and redirects to the course page:
   ```
   python test_login.py
   ```
   This will:
   - Open a Chrome browser
   - Navigate to the login page
   - Enter the credentials
   - Attempt to log in
   - Check if login was successful
   - Check if redirection to the course page was successful
   - If not, attempt to manually navigate to the course page

4. The test will pause at the end to allow you to verify that you can access the course content. Press Enter to close the browser and exit the test.

### Testing Course Navigation Functionality

1. After ensuring the database is set up and login works, run the course navigation test:
   ```
   python test_course_navigation.py
   ```
   This will:
   - Log in to the learning platform
   - Navigate to the specified course
   - Find incomplete lessons in the course
   - Determine the completion time for each lesson
   - Wait for the appropriate time for each lesson
   - Navigate to the next lesson automatically
   - Track course completion based on user settings
   - Move to the next course when the current one is completed

2. You can also run specific tests for the new functionality:
   ```
   python test_course_navigation.py --test-incomplete
   ```
   This will test only the lessons with less than 50% completion functionality, including:
   - Finding lessons using the specific XPath
   - Extracting and checking completion percentages
   - Automatically clicking on the first lesson with less than 50% completion

   ```
   python test_course_navigation.py --test-completion-time
   ```
   This will test only the lesson completion time functionality, including:
   - Finding a lesson to test
   - Checking canvas elements for timing information
   - Determining the completion time

3. The test will show detailed progress information in the console, including:
   - Which lessons are being processed
   - How much time is remaining for each lesson
   - When navigation to the next lesson occurs
   - When a course is completed and the next course begins

3. The test will pause at the end to allow you to verify the results. Press Enter to close the browser and exit the test.

## Credentials

The following credentials are used for testing:
- Username: 001097034799
- Password: 001097034799
- Login URL: https://hoclythuyetlaixe.eco-tek.com.vn/web/login
- Course URL: https://hoclythuyetlaixe.eco-tek.com.vn/slides/cau-tao-va-sua-chua-thong-thuong-xe-oto-283

## Course Navigation Features

The course navigation functionality includes the following features:

1. **Finding Lessons with Less Than 50% Completion**:
   - Uses the specific XPath `//*[@id="home"]/div/ul/li/ul/li` to find lesson elements
   - Directly processes each li element to find those with less than 50% completion
   - Examines span elements within each li to extract completion percentages
   - Also checks the li text directly for percentage indicators if no span is found
   - Identifies lessons with less than 50% completion and finds their associated URLs
   - Automatically clicks on the first lesson with less than 50% completion to start learning
   - Treats lessons without completion indicators as 0% complete (not started)
   - Falls back to alternative approaches if the direct method doesn't work

2. **Lesson Completion Time**:
   - Checks canvas elements for timing information
   - Looks for data-time attributes on canvas elements
   - Examines parent elements of canvas for timing information
   - Falls back to explicit time indicators or content-based estimation if canvas timing is not available

3. **Automatic Navigation**:
   - Uses the specific XPath `//*[@id="next-slide-button"]` to find the next button
   - Falls back to alternative selectors if the specific XPath doesn't work
   - Automatically clicks the next button after lesson completion

4. **Course Completion Tracking**:
   - Compares actual time spent with required time from user settings
   - Marks courses as completed when all lessons are finished and time requirements are met
   - Automatically moves to the next course when the current one is completed

5. **Platform-Specific Handling**:
   - Includes specialized functions for different learning platforms
   - Currently supports eco-tek.com.vn with the `process_eco_tek_course` function
   - Can be extended to support other platforms by adding new specialized functions

## Troubleshooting

If you encounter issues:

1. **ChromeDriver Issues**:
   - Make sure you have the correct version of ChromeDriver for your Chrome browser
   - The ChromeDriver should be in the chromedriver directory at the root of the project

2. **Database Connection Issues**:
   - Verify your MySQL server is running
   - Check the connection parameters in database_model.py
   - Run test_db_connection.py to diagnose any database issues

3. **Login Issues**:
   - Check if the website's login page structure has changed
   - Verify the credentials are correct
   - Look for any error messages in the console output
   - Check the error screenshot if one was generated

4. **Course Navigation Issues**:
   - If the specific XPaths don't work, the system will fall back to alternative selectors
   - Check the console output for detailed information about what the navigation model is doing
   - If a specific lesson can't be found or navigated to, you may need to update the XPaths in course_navigation_model.py
