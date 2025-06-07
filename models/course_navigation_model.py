from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
from models.course_model import Course

class CourseNavigationModel:
    def __init__(self, driver, db_model):
        """
        Initialize the CourseNavigationModel with a WebDriver instance and database model

        Args:
            driver: Selenium WebDriver instance
            db_model: Database model for storing course progress
        """
        self.driver = driver
        self.db_model = db_model
        self.wait = WebDriverWait(driver, 10)  # 10 seconds timeout

    def get_lessons_less_than_50_percent(self, course_url):
        """
        Navigate to the course page and find all lessons with completion less than 50%
        and click on the first such lesson to start learning

        Args:
            course_url (str): URL of the course page

        Returns:
            list: List of dictionaries containing lesson information (url, title)
        """
        try:
            # Navigate to the course page
            print(f"Navigating to course page: {course_url}")
            self.driver.get(course_url)
            time.sleep(3)  # Wait for page to load

            # Find all lesson links using the specific XPath provided
            lessons_less_than_50_percent = []
            first_lesson_clicked = False

            # COMPLETELY NEW APPROACH: Directly find all li elements and check their content
            print("Using new approach: Directly finding li elements and checking their content")
            try:
                # Use the specific XPath provided in the issue description to get all li elements
                li_elements = self.driver.find_elements(By.XPATH, "//*[@id=\"home\"]/div/ul/li/ul/li")
                print(f"Found {len(li_elements)} li elements using the specific XPath")

                # Process each li element to find those with less than 50% completion
                for li in li_elements:
                    try:
                        # Get the li text and extract any information
                        li_text = li.text.strip()
                        print(f"Li text: '{li_text}'")

                        # Try to find a span element within the li
                        span_elements = li.find_elements(By.TAG_NAME, "span")

                        completion_percentage = 0  # Default to 0%

                        # Check each span for progress information
                        for span in span_elements:
                            try:
                                span_text = span.text.strip()
                                print(f"Span text within li: '{span_text}'")

                                # Look for percentage pattern in the span text
                                import re
                                percentage_match = re.search(r'(\d+)\s*%', span_text)
                                if percentage_match:
                                    completion_percentage = int(percentage_match.group(1))
                                    print(f"Found completion percentage in span: {completion_percentage}%")
                                    break
                            except Exception as e:
                                print(f"Error processing span within li: {e}")

                        # If no span found or no percentage in span, try to extract from li text directly
                        if completion_percentage == 0:
                            percentage_match = re.search(r'(\d+)\s*%', li_text)
                            if percentage_match:
                                completion_percentage = int(percentage_match.group(1))
                                print(f"Found completion percentage in li text: {completion_percentage}%")

                        # Check if the completion percentage is less than 50%
                        if completion_percentage < 50:
                            print(f"Found li with <50% completion: {li_text}, Completion: {completion_percentage}%")

                            # Try to find an anchor element within the li
                            try:
                                # First try to find a direct child anchor
                                anchors = li.find_elements(By.TAG_NAME, "a")

                                # If no direct child anchors, try to find any descendant anchor
                                if not anchors:
                                    anchors = li.find_elements(By.XPATH, ".//a")

                                if anchors:
                                    anchor = anchors[0]  # Use the first anchor found
                                    lesson_url = anchor.get_attribute("href")
                                    lesson_title = li_text.replace(span_text, "").strip()  # Remove span text from li text

                                    print(f"Found lesson with <50% completion: {lesson_title}, URL: {lesson_url}, Completion: {completion_percentage}%")

                                    # Add to our list
                                    lessons_less_than_50_percent.append({
                                        'url': lesson_url,
                                        'title': lesson_title,
                                        'element': li,
                                        'completion_percentage': completion_percentage
                                    })

                                    # Click on the first lesson with <50% completion
                                    if not first_lesson_clicked:
                                        try:
                                            print(f"Clicking on lesson with <50% completion: {lesson_title}")
                                            anchor.click()
                                            first_lesson_clicked = True
                                            time.sleep(3)  # Wait for the lesson page to load
                                            break  # Exit the loop after clicking
                                        except Exception as click_error:
                                            print(f"Error clicking on lesson: {click_error}")
                                else:
                                    print(f"No anchor found in li with <50% completion")

                                    # Try to find an anchor in the parent element
                                    try:
                                        parent = li.find_element(By.XPATH, "./..")
                                        parent_anchors = parent.find_elements(By.TAG_NAME, "a")

                                        if parent_anchors:
                                            anchor = parent_anchors[0]
                                            lesson_url = anchor.get_attribute("href")
                                            lesson_title = li_text.replace(span_text, "").strip()

                                            print(f"Found lesson with <50% completion (via parent): {lesson_title}, URL: {lesson_url}, Completion: {completion_percentage}%")

                                            # Add to our list
                                            lessons_less_than_50_percent.append({
                                                'url': lesson_url,
                                                'title': lesson_title,
                                                'element': parent,
                                                'completion_percentage': completion_percentage
                                            })

                                            # Click on the first lesson with <50% completion
                                            if not first_lesson_clicked:
                                                try:
                                                    print(f"Clicking on lesson with <50% completion: {lesson_title}")
                                                    anchor.click()
                                                    first_lesson_clicked = True
                                                    time.sleep(3)  # Wait for the lesson page to load
                                                    break  # Exit the loop after clicking
                                                except Exception as click_error:
                                                    print(f"Error clicking on lesson: {click_error}")
                                    except Exception as e:
                                        print(f"Error finding anchor in parent: {e}")
                            except Exception as e:
                                print(f"Error finding anchor in li: {e}")
                    except Exception as e:
                        print(f"Error processing li element: {e}")

                # If we found lessons with <50% completion, return them
                if lessons_less_than_50_percent:
                    print(f"Found {len(lessons_less_than_50_percent)} lessons with <50% completion")
                    return lessons_less_than_50_percent

                # If we didn't find any using the new approach, try the original approach
                print("No lessons with <50% completion found using new approach, trying original approach")
            except Exception as e:
                print(f"Error with new approach: {e}")
                print("Trying original approach")

            # Original approach as fallback
            try:
                # Use the specific XPath provided in the issue description
                lesson_elements = self.driver.find_elements(By.XPATH, "//*[@id=\"home\"]/div/ul/li/ul/li")

                # If the specific XPath doesn't work, fall back to alternative selectors
                if not lesson_elements:
                    print("Specific XPath didn't find any lessons, trying alternatives...")
                    # Look for lesson links in the sidebar or content area
                    lesson_elements = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'lesson') or contains(@class, 'chapter')]")

                if not lesson_elements:
                    # Try alternative selectors if the above doesn't work
                    lesson_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'sidebar')]//a")

                if not lesson_elements:
                    # Another alternative
                    lesson_elements = self.driver.find_elements(By.XPATH, "//ul[contains(@class, 'lessons')]//a")

                # For eco-tek.com.vn specifically
                if not lesson_elements:
                    lesson_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'list-group')]//a")

                print(f"Found {len(lesson_elements)} potential lesson elements using fallback method")

                for element in lesson_elements:
                    try:
                        lesson_url = element.get_attribute('href')
                        lesson_title = element.text.strip()

                        # Check the completion percentage for this lesson using the span element
                        # Use the specific XPath provided in the issue description
                        completion_percentage = 0  # Default to 0% if we can't determine

                        try:
                            # First approach: Use the specific XPath for the span element
                            span_elements = element.find_elements(By.XPATH, "./span")

                            if span_elements:
                                for span in span_elements:
                                    try:
                                        span_text = span.text.strip()
                                        import re
                                        percentage_match = re.search(r'(\d+)\s*%', span_text)
                                        if percentage_match:
                                            completion_percentage = int(percentage_match.group(1))
                                            print(f"Found completion percentage from span text: {completion_percentage}%")
                                            break
                                    except Exception as e:
                                        print(f"Error extracting percentage from span: {e}")
                            else:
                                # If no span elements found directly, try the full XPath
                                # This is a fallback in case the relative XPath doesn't work
                                li_id = element.get_attribute("id")
                                if li_id:
                                    full_xpath = f"//*[@id='{li_id}']/span"
                                    try:
                                        span_elements = self.driver.find_elements(By.XPATH, full_xpath)
                                        if span_elements:
                                            for span in span_elements:
                                                span_text = span.text.strip()
                                                import re
                                                percentage_match = re.search(r'(\d+)\s*%', span_text)
                                                if percentage_match:
                                                    completion_percentage = int(percentage_match.group(1))
                                                    print(f"Found completion percentage from full XPath span: {completion_percentage}%")
                                                    break
                                    except Exception as e:
                                        print(f"Error with full XPath approach: {e}")

                            # If still no percentage found, fall back to the original methods
                            if completion_percentage == 0:
                                # Look for completion percentage indicators
                                completion_indicators = element.find_elements(By.XPATH, ".//*[contains(@class, 'progress') or contains(@class, 'percent')]")

                                for indicator in completion_indicators:
                                    try:
                                        # Try to extract percentage from text (e.g., "50%")
                                        indicator_text = indicator.text.strip()
                                        percentage_match = re.search(r'(\d+)\s*%', indicator_text)
                                        if percentage_match:
                                            completion_percentage = int(percentage_match.group(1))
                                            print(f"Found completion percentage from indicator text: {completion_percentage}%")
                                            break

                                        # Try to extract percentage from style attribute (e.g., "width: 50%")
                                        progress_value = indicator.get_attribute('style')
                                        if progress_value:
                                            percentage_match = re.search(r'width:\s*(\d+)\s*%', progress_value)
                                            if percentage_match:
                                                completion_percentage = int(percentage_match.group(1))
                                                print(f"Found completion percentage from style: {completion_percentage}%")
                                                break

                                        # Try to extract percentage from data attributes
                                        data_progress = indicator.get_attribute('data-progress')
                                        if data_progress:
                                            try:
                                                # Handle both decimal (0.5) and percentage (50) formats
                                                progress_value = float(data_progress)
                                                if progress_value <= 1:  # It's in decimal format (0.0 to 1.0)
                                                    completion_percentage = int(progress_value * 100)
                                                else:  # It's already a percentage
                                                    completion_percentage = int(progress_value)
                                                print(f"Found completion percentage from data attribute: {completion_percentage}%")
                                                break
                                            except ValueError:
                                                pass
                                    except Exception as e:
                                        print(f"Error extracting completion percentage: {e}")
                                        continue
                        except Exception as e:
                            print(f"Error in span-based percentage extraction: {e}")
                            # Continue with the original approach as fallback

                        # Check if the lesson is less than 50% complete
                        is_less_than_50_percent = completion_percentage < 50

                        # Also check if there are any completion indicators at all
                        if not completion_indicators:
                            # If there are no indicators, we'll assume it's not started (0%)
                            is_less_than_50_percent = True

                        if is_less_than_50_percent and lesson_url:
                            lessons_less_than_50_percent.append({
                                'url': lesson_url,
                                'title': lesson_title,
                                'element': element,
                                'completion_percentage': completion_percentage
                            })
                            print(f"Found lesson with <50% completion: {lesson_title} - {lesson_url} ({completion_percentage}%)")

                            # Click on the first lesson with <50% completion if we haven't clicked on one yet
                            if not first_lesson_clicked:
                                try:
                                    print(f"Clicking on lesson with <50% completion: {lesson_title}")
                                    element.click()
                                    first_lesson_clicked = True
                                    time.sleep(3)  # Wait for the lesson page to load
                                except Exception as click_error:
                                    print(f"Error clicking on lesson: {click_error}")
                    except Exception as e:
                        print(f"Error processing lesson element: {e}")
                        continue

            except Exception as e:
                print(f"Error finding lesson elements: {e}")

            return lessons_less_than_50_percent

        except Exception as e:
            print(f"Error navigating to course page: {e}")
            return []

    def get_lesson_completion_time(self, lesson_url):
        """
        Navigate to a lesson and determine how long it takes to complete

        Args:
            lesson_url (str): URL of the lesson

        Returns:
            int: Estimated completion time in seconds
        """
        try:
            # Navigate to the lesson page
            print(f"Navigating to lesson page: {lesson_url}")
            self.driver.get(lesson_url)
            time.sleep(3)  # Wait for page to load

            # Look for completion time indicators
            completion_time = 0

            try:
                # Check canvas elements for timing as specified in the issue description
                canvas_elements = self.driver.find_elements(By.XPATH, "//canvas")
                if canvas_elements:
                    print(f"Found {len(canvas_elements)} canvas elements")

                    # Try to get timing information from canvas attributes or parent elements
                    for canvas in canvas_elements:
                        try:
                            # Check for data attributes that might contain timing information
                            data_time = canvas.get_attribute('data-time')
                            if data_time and data_time.isdigit():
                                completion_time = int(data_time)
                                print(f"Found completion time from canvas data-time attribute: {completion_time} seconds")
                                break

                            # Check for parent elements with timing information
                            parent = canvas.find_element(By.XPATH, "./..")
                            parent_text = parent.text

                            # Look for time indicators in the parent text
                            import re
                            time_matches = re.findall(r'(\d+)\s*(min|minute|phút)', parent_text, re.IGNORECASE)
                            if time_matches:
                                # Convert minutes to seconds
                                completion_time = int(time_matches[0][0]) * 60
                                print(f"Found completion time from canvas parent element: {completion_time} seconds")
                                break
                        except Exception as e:
                            print(f"Error checking canvas element for timing: {e}")
                            continue

                # If no timing information found from canvas elements, try other methods
                if completion_time == 0:
                    # Try to find an explicit completion time indicator
                    time_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'min') or contains(text(), 'minutes') or contains(text(), 'phút')]")
                    time_text = time_element.text

                    # Extract numbers from the text
                    import re
                    numbers = re.findall(r'\d+', time_text)
                    if numbers:
                        # Convert minutes to seconds
                        completion_time = int(numbers[0]) * 60
                        print(f"Found explicit completion time: {completion_time} seconds")
            except NoSuchElementException:
                # If no explicit indicator, estimate based on content length
                content_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'content') or contains(@class, 'lesson-content')]")
                if content_elements:
                    # Rough estimate: 5 seconds per line of text
                    text_lines = content_elements[0].text.count('\n') + 1
                    completion_time = text_lines * 5
                    print(f"Estimated completion time based on content: {completion_time} seconds")
                else:
                    # Default to 5 minutes if we can't determine
                    completion_time = 300
                    print(f"Using default completion time: {completion_time} seconds")

            # If completion time is unreasonably short, set a minimum
            if completion_time < 60:
                completion_time = 60

            return completion_time

        except Exception as e:
            print(f"Error determining lesson completion time: {e}")
            # Default to 5 minutes
            return 300

    def navigate_to_next_lesson(self, current_lesson_url):
        """
        Navigate to the next lesson after the current one

        Args:
            current_lesson_url (str): URL of the current lesson

        Returns:
            str: URL of the next lesson, or None if there is no next lesson
        """
        try:
            # Make sure we're on the current lesson page
            if self.driver.current_url != current_lesson_url:
                self.driver.get(current_lesson_url)
                time.sleep(3)  # Wait for page to load

            # Look for next lesson button using the specific XPath provided
            try:
                # Use the specific XPath provided in the issue description
                next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                print("Found next button using the specific XPath")
                next_buttons = [next_button]
            except NoSuchElementException:
                print("Specific XPath for next button not found, trying alternatives...")
                # Fall back to alternative selectors if the specific XPath doesn't work
                next_buttons = []

                # Try various selectors that might indicate a "next" button
                selectors = [
                    "//a[contains(text(), 'Next') or contains(text(), 'next') or contains(text(), 'Tiếp theo')]",
                    "//button[contains(text(), 'Next') or contains(text(), 'next') or contains(text(), 'Tiếp theo')]",
                    "//a[contains(@class, 'next')]",
                    "//button[contains(@class, 'next')]",
                    "//a[contains(@title, 'Next') or contains(@title, 'next') or contains(@title, 'Tiếp theo')]",
                    "//i[contains(@class, 'fa-arrow-right')]/parent::a",
                    "//i[contains(@class, 'fa-chevron-right')]/parent::a"
                ]

                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        next_buttons.extend(elements)
                    except:
                        continue

            if next_buttons:
                # Click the first "next" button found
                next_url = next_buttons[0].get_attribute('href')
                print(f"Found next lesson button. URL: {next_url}")
                next_buttons[0].click()
                time.sleep(3)  # Wait for page to load

                # Return the URL of the next lesson
                return self.driver.current_url
            else:
                print("No next lesson button found")
                return None

        except Exception as e:
            print(f"Error navigating to next lesson: {e}")
            return None

    def wait_for_lesson_completion(self, completion_time):
        """
        Wait for the specified completion time for a lesson

        Args:
            completion_time (int): Time to wait in seconds

        Returns:
            bool: True if wait completed successfully
        """
        try:
            print(f"Waiting {completion_time} seconds for lesson completion...")

            # Instead of a simple sleep, we'll check every 5 seconds if the user wants to skip
            # This allows for manual intervention if needed
            start_time = time.time()
            elapsed_time = 0

            while elapsed_time < completion_time:
                time.sleep(5)  # Check every 5 seconds
                elapsed_time = time.time() - start_time
                remaining_time = completion_time - elapsed_time
                print(f"Lesson completion: {int(elapsed_time)} seconds elapsed, {int(remaining_time)} seconds remaining")

                # Here you could add a check for a UI element that allows skipping
                # For now, we'll just wait the full time

            print("Lesson completion time reached")
            return True

        except Exception as e:
            print(f"Error during lesson completion wait: {e}")
            return False

    def check_course_completion(self, user_id, course_id):
        """
        Check if a course is completed based on user settings

        Args:
            user_id (int): ID of the user
            course_id (int): ID of the course

        Returns:
            bool: True if the course is completed
        """
        try:
            # Get the course from the database
            courses = self.db_model.get_courses_for_user(user_id)
            course = next((c for c in courses if c.id == course_id), None)
            print(f"GEt {courses} and course {course}")
            if not course:
                print(f"Course with ID {course_id} not found for user {user_id}")
                return False

            # Get the user's settings
            users = self.db_model.get_all_users()
            user = next((u for u in users if u.id == user_id), None)

            if not user:
                print(f"User with ID {user_id} not found")
                return False

            # Check if the course is marked as completed
            if course.is_completed:
                print(f"Course {course.name} is already marked as completed")
                return True

            # Check if the user has spent enough time on the course
            # This assumes that running_time is in seconds and hours is in hours
            required_time_seconds = user.hours * 3600  # Convert hours to seconds

            if user.running_time >= required_time_seconds:
                print(f"User has spent enough time on the course: {user.running_time} seconds >= {required_time_seconds} seconds")

                # Mark the course as completed
                course.is_completed = 1
                self.db_model.update_course(course.id, course)

                return True
            else:
                print(f"User has not spent enough time on the course: {user.running_time} seconds < {required_time_seconds} seconds")
                return False

        except Exception as e:
            print(f"Error checking course completion: {e}")
            return False

    def move_to_next_course(self, user_id, current_course_id):
        """
        Move to the next course after the current one is completed

        Args:
            user_id (int): ID of the user
            current_course_id (int): ID of the current course

        Returns:
            Course: Next course object, or None if there is no next course
        """
        try:
            # Get all courses for the user
            courses = self.db_model.get_courses_for_user(user_id)

            if not courses:
                print(f"No courses found for user {user_id}")
                return None

            # Sort courses by ID to maintain order
            courses.sort(key=lambda c: c.id)

            # Find the current course in the list
            current_index = next((i for i, c in enumerate(courses) if c.id == current_course_id), -1)

            if current_index == -1:
                print(f"Current course with ID {current_course_id} not found")
                return None

            # Check if there's a next course
            if current_index < len(courses) - 1:
                next_course = courses[current_index + 1]
                print(f"Moving to next course: {next_course.name}")

                # Navigate to the next course
                self.driver.get(next_course.url)
                time.sleep(3)  # Wait for page to load

                return next_course
            else:
                print("No more courses available")
                return None

        except Exception as e:
            print(f"Error moving to next course: {e}")
            return None

    # Function to handle different learning center approaches
    def process_eco_tek_course(self, course_url, user_id, course_id):
        """
        Process a course on the eco-tek.com.vn platform

        Args:
            course_url (str): URL of the course
            user_id (int): ID of the user
            course_id (int): ID of the course

        Returns:
            bool: True if processing was successful
        """
        try:
            print(f"Processing eco-tek course: {course_url}")

            # Navigate to the course page
            self.driver.get(course_url)
            time.sleep(3)  # Wait for page to load

            # Get lessons with less than 50% completion
            lessons_less_than_50_percent = self.get_lessons_less_than_50_percent(course_url)
            print(f"count lessons: {lessons_less_than_50_percent}")
            if not lessons_less_than_50_percent:
                print("No lessons with less than 50% completion found. Course may be completed.")

                # Mark the course as completed
                courses = self.db_model.get_courses_for_user(user_id)
                course = next((c for c in courses if c.id == course_id), None)

                if course:
                    course.is_completed = 1
                    self.db_model.update_course(course_id, course)
                    print(f"Marked course {course.name} as completed")

                # Check if we should move to the next course
                if self.check_course_completion(user_id, course_id):
                    next_course = self.move_to_next_course(user_id, course_id)
                    if next_course:
                        # Recursively process the next course
                        return self.process_eco_tek_course(next_course.url, user_id, next_course.id)

                return True

            # Process each lesson with less than 50% completion
            for lesson in lessons_less_than_50_percent:
                print(f"Processing lesson: {lesson['title']}")

                # Navigate to the lesson
                self.driver.get(lesson['url'])
                time.sleep(3)  # Wait for page to load

                # Update current lesson in the database
                courses = self.db_model.get_courses_for_user(user_id)
                course = next((c for c in courses if c.id == course_id), None)

                if course:
                    course.current_lesson = lesson['url']
                    self.db_model.update_course(course_id, course)

                # Get the completion time for this lesson
                completion_time = self.get_lesson_completion_time(lesson['url'])

                # Wait for the lesson to complete
                self.wait_for_lesson_completion(completion_time)

                # Navigate to the next lesson
                next_lesson_url = self.navigate_to_next_lesson(lesson['url'])

                if not next_lesson_url:
                    print("No next lesson found. This may be the last lesson.")
                    break

            # Check if the course is completed
            if self.check_course_completion(user_id, course_id):
                next_course = self.move_to_next_course(user_id, course_id)
                if next_course:
                    # Recursively process the next course
                    return self.process_eco_tek_course(next_course.url, user_id, next_course.id)

            return True

        except Exception as e:
            print(f"Error processing eco-tek course: {e}")
            return False
