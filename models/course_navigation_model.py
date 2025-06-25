from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import datetime
import os
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
            time.sleep(5)  # Increased wait time for page to load completely

            # Find all lesson links using multiple XPath approaches
            lessons_less_than_50_percent = []
            first_lesson_clicked = False

            # ROBUST APPROACH: Try multiple XPath patterns to find lesson elements
            print("Using robust approach: Trying multiple XPath patterns to find lesson elements")

            # Try multiple XPath patterns to find lesson elements
            try:
                # List of XPath patterns to try
                xpath_patterns = [
                    "//*[@id=\"home\"]/div/ul/li/ul/li",  # Original XPath
                    "//li[contains(@class, 'o_wslides_lesson_list_item')]",  # Class-based XPath
                    "//li[contains(@class, 'lesson')]",  # Generic lesson class
                    "//a[contains(@class, 'o_wslides_js_slides_list_slide_link')]",  # Direct lesson links
                    "//div[contains(@class, 'o_wslides_lesson_content')]//li",  # Lesson content container
                    "//ul[contains(@class, 'o_wslides_lesson_list')]/li",  # Lesson list items
                    "//li[.//span[contains(text(), '%')]]"  # Any li containing a span with percentage
                ]

                li_elements = []

                # Try each XPath pattern until we find elements
                for xpath in xpath_patterns:
                    try:
                        print(f"Trying XPath pattern: {xpath}")
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        if elements:
                            print(f"Found {len(elements)} elements using XPath: {xpath}")
                            li_elements = elements
                            break
                    except Exception as e:
                        print(f"Error with XPath pattern {xpath}: {e}")

                # If no elements found with any XPath, try a more generic approach
                if not li_elements:
                    print("No elements found with specific XPaths, trying generic approach")
                    try:
                        # Look for any links that might be lessons
                        li_elements = self.driver.find_elements(By.TAG_NAME, "a")
                        print(f"Found {len(li_elements)} anchor elements as fallback")
                    except Exception as e:
                        print(f"Error with generic approach: {e}")

                print(f"Found {len(li_elements)} potential lesson elements")

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
                                            # Store the current URL before clicking
                                            before_url = self.driver.current_url

                                            # Try clicking the anchor
                                            anchor.click()
                                            first_lesson_clicked = True
                                            time.sleep(5)  # Increased wait time for the lesson page to load

                                            # Check if the page changed
                                            after_url = self.driver.current_url
                                            if after_url == before_url:
                                                print(f"Warning: URL did not change after clicking. Before: {before_url}, After: {after_url}")
                                                # Try direct navigation as fallback
                                                if lesson_url:
                                                    print(f"Trying direct navigation to lesson URL: {lesson_url}")
                                                    self.driver.get(lesson_url)
                                                    time.sleep(5)  # Wait for page to load

                                            # Check if we got a blank page (no content)
                                            page_source = self.driver.page_source
                                            if len(page_source.strip()) < 100 or "404" in page_source or "not found" in page_source.lower():
                                                print(f"Warning: Possible blank page or error page detected. Page source length: {len(page_source.strip())}")
                                                # Try direct navigation as fallback
                                                if lesson_url:
                                                    print(f"Trying direct navigation to lesson URL: {lesson_url}")
                                                    self.driver.get(lesson_url)
                                                    time.sleep(5)  # Wait for page to load

                                            break  # Exit the loop after clicking
                                        except Exception as click_error:
                                            print(f"Error clicking on lesson: {click_error}")
                                            # Try direct navigation as fallback
                                            if lesson_url:
                                                try:
                                                    print(f"Trying direct navigation to lesson URL after click error: {lesson_url}")
                                                    self.driver.get(lesson_url)
                                                    first_lesson_clicked = True
                                                    time.sleep(5)  # Wait for page to load
                                                    break  # Exit the loop after navigation
                                                except Exception as nav_error:
                                                    print(f"Error navigating directly to lesson URL: {nav_error}")
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
                                                    print(f"Clicking on lesson with <50% completion (via parent): {lesson_title}")
                                                    # Store the current URL before clicking
                                                    before_url = self.driver.current_url

                                                    # Try clicking the anchor
                                                    anchor.click()
                                                    first_lesson_clicked = True
                                                    time.sleep(5)  # Increased wait time for the lesson page to load

                                                    # Check if the page changed
                                                    after_url = self.driver.current_url
                                                    if after_url == before_url:
                                                        print(f"Warning: URL did not change after clicking parent. Before: {before_url}, After: {after_url}")
                                                        # Try direct navigation as fallback
                                                        if lesson_url:
                                                            print(f"Trying direct navigation to lesson URL (parent): {lesson_url}")
                                                            self.driver.get(lesson_url)
                                                            time.sleep(5)  # Wait for page to load

                                                    # Check if we got a blank page (no content)
                                                    page_source = self.driver.page_source
                                                    if len(page_source.strip()) < 100 or "404" in page_source or "not found" in page_source.lower():
                                                        print(f"Warning: Possible blank page or error page detected (parent). Page source length: {len(page_source.strip())}")
                                                        # Try direct navigation as fallback
                                                        if lesson_url:
                                                            print(f"Trying direct navigation to lesson URL (parent): {lesson_url}")
                                                            self.driver.get(lesson_url)
                                                            time.sleep(5)  # Wait for page to load

                                                    break  # Exit the loop after clicking
                                                except Exception as click_error:
                                                    print(f"Error clicking on lesson (parent): {click_error}")
                                                    # Try direct navigation as fallback
                                                    if lesson_url:
                                                        try:
                                                            print(f"Trying direct navigation to lesson URL after parent click error: {lesson_url}")
                                                            self.driver.get(lesson_url)
                                                            first_lesson_clicked = True
                                                            time.sleep(5)  # Wait for page to load
                                                            break  # Exit the loop after navigation
                                                        except Exception as nav_error:
                                                            print(f"Error navigating directly to lesson URL (parent): {nav_error}")
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
                                    print(f"Clicking on lesson with <50% completion (fallback): {lesson_title}")
                                    # Store the current URL before clicking
                                    before_url = self.driver.current_url

                                    # Try clicking the element
                                    element.click()
                                    first_lesson_clicked = True
                                    time.sleep(5)  # Increased wait time for the lesson page to load

                                    # Check if the page changed
                                    after_url = self.driver.current_url
                                    if after_url == before_url:
                                        print(f"Warning: URL did not change after clicking (fallback). Before: {before_url}, After: {after_url}")
                                        # Try direct navigation as fallback
                                        if lesson_url:
                                            print(f"Trying direct navigation to lesson URL (fallback): {lesson_url}")
                                            self.driver.get(lesson_url)
                                            time.sleep(5)  # Wait for page to load

                                    # Check if we got a blank page (no content)
                                    page_source = self.driver.page_source
                                    if len(page_source.strip()) < 100 or "404" in page_source or "not found" in page_source.lower():
                                        print(f"Warning: Possible blank page or error page detected (fallback). Page source length: {len(page_source.strip())}")
                                        # Try direct navigation as fallback
                                        if lesson_url:
                                            print(f"Trying direct navigation to lesson URL (fallback): {lesson_url}")
                                            self.driver.get(lesson_url)
                                            time.sleep(5)  # Wait for page to load
                                except Exception as click_error:
                                    print(f"Error clicking on lesson (fallback): {click_error}")
                                    # Try direct navigation as fallback
                                    if lesson_url:
                                        try:
                                            print(f"Trying direct navigation to lesson URL after fallback click error: {lesson_url}")
                                            self.driver.get(lesson_url)
                                            first_lesson_clicked = True
                                            time.sleep(5)  # Wait for page to load
                                        except Exception as nav_error:
                                            print(f"Error navigating directly to lesson URL (fallback): {nav_error}")
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
        Navigate to the next lesson after the current one.
        If the next lesson is already completed, continue to the next lesson again.

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

            # First, click the next button to go to the next lesson
            next_lesson_url = self._click_next_button()
            if not next_lesson_url:
                return None

            # Check if the next lesson is already completed
            max_attempts = 5  # Limit the number of automatic next clicks to avoid infinite loops
            attempts = 0

            while attempts < max_attempts and self._is_lesson_completed():
                print("[LESSON STATUS] Next lesson is already completed, clicking next again")
                next_lesson_url = self._click_next_button()
                if not next_lesson_url:
                    break
                attempts += 1

            if attempts >= max_attempts:
                print(f"[LESSON STATUS] Reached maximum number of automatic next clicks ({max_attempts})")

            return next_lesson_url

        except Exception as e:
            print(f"[LESSON STATUS] Error navigating to next lesson: {e}")
            return None

    def wait_for_lesson_completion(self, completion_time):
        """
        Wait for the specified completion time for a lesson or until the countdown timer has finished

        Args:
            completion_time (int): Time to wait in seconds

        Returns:
            bool: True if wait completed successfully
        """
        try:
            print(f"[LESSON STATUS] Waiting for lesson completion (max {completion_time} seconds)...")

            # Instead of a simple sleep, we'll check every 5 seconds if the countdown timer has finished
            start_time = time.time()
            elapsed_time = 0

            while elapsed_time < completion_time:
                time.sleep(5)  # Check every 5 seconds
                elapsed_time = time.time() - start_time
                remaining_time = completion_time - elapsed_time
                print(f"[LESSON STATUS] Lesson completion: {int(elapsed_time)} seconds elapsed, {int(remaining_time)} seconds remaining")

                # Check if the countdown timer element exists
                try:
                    # First find the section element using the XPath from the issue description
                    section_element = self.driver.find_element(By.XPATH, "//*[@id=\"oe_structure_website_slides_lesson_top_1\"]/section")
                    print(f"[LESSON STATUS] Found countdown section element at {datetime.datetime.now().strftime('%H:%M:%S')}")

                    # Log all data attributes of the section element
                    section_class = section_element.get_attribute("class")
                    data_display = section_element.get_attribute("data-display")
                    data_end_action = section_element.get_attribute("data-end-action")
                    data_size = section_element.get_attribute("data-size")
                    data_layout = section_element.get_attribute("data-layout")
                    data_snippet = section_element.get_attribute("data-snippet")
                    data_end_time = section_element.get_attribute("data-end-time")
                    data_name = section_element.get_attribute("data-name")

                    print(f"[LESSON STATUS] Section class: {section_class}")
                    print(f"[LESSON STATUS] Section data attributes:")
                    print(f"[LESSON STATUS]   - data-display: {data_display}")
                    print(f"[LESSON STATUS]   - data-end-action: {data_end_action}")
                    print(f"[LESSON STATUS]   - data-size: {data_size}")
                    print(f"[LESSON STATUS]   - data-layout: {data_layout}")
                    print(f"[LESSON STATUS]   - data-snippet: {data_snippet}")
                    print(f"[LESSON STATUS]   - data-end-time: {data_end_time}")
                    print(f"[LESSON STATUS]   - data-name: {data_name}")
                    if data_end_time:
                        try:
                            end_time_float = float(data_end_time)
                            current_time = time.time()
                            remaining_seconds = max(0, end_time_float - current_time)
                            minutes, seconds = divmod(int(remaining_seconds), 60)
                            print(f"[LESSON STATUS] Countdown timer end time: {data_end_time}")
                            print(f"[LESSON STATUS] Countdown timer remaining time: {minutes}:{seconds:02d} ({int(remaining_seconds)} seconds)")
                        except ValueError:
                            print(f"[LESSON STATUS] Could not convert data-end-time to float: {data_end_time}")

                    # Then find the div containing the canvas elements
                    countdown_section = section_element.find_element(By.XPATH, ".//div/div")
                    print(f"[LESSON STATUS] Found countdown canvas wrapper at {datetime.datetime.now().strftime('%H:%M:%S')}")

                    # Try to find the canvas element or any timer display within the countdown section
                    # The HTML structure shows canvas elements within a div with class "ect_countdown_canvas_wrapper"
                    canvas_elements = countdown_section.find_elements(By.TAG_NAME, "canvas")
                    print(f"[LESSON STATUS] Found {len(canvas_elements)} canvas elements in countdown wrapper")

                    # Log details about each canvas element
                    for i, canvas in enumerate(canvas_elements):
                        try:
                            canvas_width = canvas.get_attribute("width")
                            canvas_height = canvas.get_attribute("height")
                            canvas_class = canvas.get_attribute("class")
                            print(f"[LESSON STATUS] Canvas {i+1}: width={canvas_width}, height={canvas_height}, class={canvas_class}")

                            # Try to get parent element with class ect_countdown_canvas_flex
                            parent = canvas.find_element(By.XPATH, "./..")
                            parent_class = parent.get_attribute("class")
                            parent_text = parent.text.strip() if parent.text else "No text"
                            print(f"[LESSON STATUS] Canvas {i+1} parent: class={parent_class}, text='{parent_text}'")
                        except Exception as e:
                            print(f"[LESSON STATUS] Error getting canvas {i+1} details: {e}")

                    # Also look for elements with class containing "ect_countdown"
                    timer_displays = countdown_section.find_elements(By.XPATH, ".//*[contains(@class, 'time') or contains(@class, 'timer') or contains(@class, 'countdown') or contains(@class, 'ect_countdown')]")
                    print(f"[LESSON STATUS] Found {len(timer_displays)} timer display elements")

                    # Extract and log the timer value if found
                    timer_text = "Unknown"
                    timer_seconds = -1  # Unknown timer value

                    if canvas_elements:
                        print(f"[LESSON STATUS] Found {len(canvas_elements)} canvas elements in countdown section")
                        # Try to get timer value from surrounding elements
                        for canvas in canvas_elements:
                            try:
                                # Check if the canvas is within a div with class "ect_countdown_canvas_flex"
                                parent = canvas.find_element(By.XPATH, "./..")
                                parent_class = parent.get_attribute("class")
                                if parent_class and "ect_countdown_canvas_flex" in parent_class:
                                    print(f"[LESSON STATUS] Found canvas in ect_countdown_canvas_flex div")

                                # Check for text in the parent element
                                if parent.text and len(parent.text.strip()) > 0:
                                    timer_text = parent.text.strip()
                                    print(f"[LESSON STATUS] Canvas parent text: '{timer_text}'")

                                    # Try to extract time values from the text
                                    import re
                                    time_match = re.search(r'(\d+):(\d+)', timer_text)
                                    if time_match:
                                        minutes = int(time_match.group(1))
                                        seconds = int(time_match.group(2))
                                        timer_seconds = minutes * 60 + seconds
                                        print(f"[LESSON STATUS] Extracted time from canvas parent: {minutes}:{seconds:02d} ({timer_seconds} seconds remaining)")

                                # If no text found in parent, try to get data attributes from the canvas
                                if timer_seconds < 0:
                                    data_time = canvas.get_attribute("data-time")
                                    if data_time and data_time.isdigit():
                                        timer_seconds = int(data_time)
                                        print(f"[LESSON STATUS] Extracted time from canvas data-time attribute: {timer_seconds} seconds remaining")

                                    # If timer is at or near zero, click the next button
                                    if "0:00" in timer_text.lower() or "00:00" in timer_text.lower() or (timer_seconds >= 0 and timer_seconds <= 1):
                                        print(f"[LESSON STATUS] Canvas timer appears to be finished: '{timer_text}'")
                                        print(f"[LESSON STATUS] Will click next button at {datetime.datetime.now().strftime('%H:%M:%S')}")

                                        # Also check if the data-end-time has passed
                                        data_end_time = section_element.get_attribute("data-end-time")
                                        if data_end_time:
                                            try:
                                                end_time_float = float(data_end_time)
                                                current_time = time.time()
                                                if current_time >= end_time_float:
                                                    print(f"[LESSON STATUS] Countdown timer has ended (data-end-time: {data_end_time}, current time: {current_time})")
                                            except ValueError:
                                                print(f"[LESSON STATUS] Could not convert data-end-time to float: {data_end_time}")

                                        # Also check if the wrapper div has a class indicating completion
                                        wrapper = countdown_section
                                        wrapper_class = wrapper.get_attribute("class")
                                        if wrapper_class and ("completed" in wrapper_class or "finished" in wrapper_class):
                                            print(f"[LESSON STATUS] Found completion indicator in wrapper class: {wrapper_class}")

                                        # Try to find and click the next button
                                        try:
                                            next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                                            if next_button.is_enabled() and next_button.is_displayed():
                                                next_button.click()
                                                time.sleep(3)  # Wait for page to load
                                                print(f"[LESSON STATUS] Clicked next button from canvas timer, now at URL: {self.driver.current_url}")

                                                # Check if the next lesson is already completed
                                                if self._is_lesson_completed():
                                                    print("[LESSON STATUS] Next lesson is already completed, clicking next again")
                                                    self._click_next_button()

                                                return True
                                        except NoSuchElementException:
                                            print("[LESSON STATUS] Next button not found after canvas timer finished")
                                        except Exception as click_error:
                                            print(f"[LESSON STATUS] Error clicking next button from canvas timer: {click_error}")

                                    break
                            except Exception as canvas_error:
                                print(f"[LESSON STATUS] Error processing canvas element: {canvas_error}")
                    elif timer_displays:
                        for display in timer_displays:
                            if display.text and len(display.text.strip()) > 0:
                                timer_text = display.text.strip()
                                print(f"[LESSON STATUS] Timer display text: '{timer_text}'")

                                # Try to extract time values from the text
                                import re
                                time_match = re.search(r'(\d+):(\d+)', timer_text)
                                if time_match:
                                    minutes = int(time_match.group(1))
                                    seconds = int(time_match.group(2))
                                    timer_seconds = minutes * 60 + seconds
                                    print(f"[LESSON STATUS] Extracted time from timer display: {minutes}:{seconds:02d} ({timer_seconds} seconds remaining)")

                                break

                    if timer_seconds >= 0:
                        print(f"[LESSON STATUS] Current timer value: {timer_text} ({timer_seconds} seconds remaining), {int(remaining_time)} seconds until auto-click")
                    else:
                        print(f"[LESSON STATUS] Current timer value: {timer_text}, {int(remaining_time)} seconds until auto-click")

                    # Check if the countdown has finished
                    # This could be determined by various means depending on the website's implementation
                    # For example, checking if a specific class is present, or if the text has changed

                    # Try to find any countdown elements within the section
                    countdown_elements = countdown_section.find_elements(By.XPATH, ".//*[contains(@class, 'countdown') or contains(@class, 'timer') or contains(@class, 'ect_countdown')]")

                    # Also look for the specific canvas elements mentioned in the issue description
                    canvas_wrapper = countdown_section.find_elements(By.XPATH, "./div[contains(@class, 'ect_countdown_canvas_wrapper')]")
                    if canvas_wrapper:
                        print(f"[LESSON STATUS] Found ect_countdown_canvas_wrapper div with {len(canvas_wrapper)} elements")

                        # Check canvas elements within the wrapper
                        wrapper_canvases = canvas_wrapper[0].find_elements(By.TAG_NAME, "canvas")
                        if wrapper_canvases:
                            print(f"[LESSON STATUS] Found {len(wrapper_canvases)} canvas elements in ect_countdown_canvas_wrapper")

                            # Check if any of the canvas elements have attributes indicating completion
                            for canvas in wrapper_canvases:
                                try:
                                    # Check for data attributes that might indicate completion
                                    data_complete = canvas.get_attribute("data-complete")
                                    data_finished = canvas.get_attribute("data-finished")
                                    data_percent = canvas.get_attribute("data-percent")

                                    if data_complete == "true" or data_finished == "true" or (data_percent and float(data_percent) >= 100):
                                        print(f"[LESSON STATUS] Canvas element indicates countdown is complete: data-complete={data_complete}, data-finished={data_finished}, data-percent={data_percent}")

                                        # Try to find and click the next button
                                        try:
                                            next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                                            if next_button.is_enabled() and next_button.is_displayed():
                                                next_button.click()
                                                time.sleep(3)  # Wait for page to load
                                                print(f"[LESSON STATUS] Clicked next button after canvas completion, now at URL: {self.driver.current_url}")
                                                return True
                                        except Exception as e:
                                            print(f"[LESSON STATUS] Error clicking next button after canvas completion: {e}")
                                except Exception as e:
                                    print(f"[LESSON STATUS] Error checking canvas attributes: {e}")

                    if not countdown_elements:
                        # If no specific countdown elements found, check if the section is still visible
                        # or if it has a specific attribute indicating completion

                        # If the countdown section is no longer visible or has changed, assume it's finished
                        print("[LESSON STATUS] No countdown elements found, checking if section is still active")

                        # Check if the next button is enabled, which might indicate the countdown is finished
                        try:
                            next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                            if next_button.is_enabled() and next_button.is_displayed():
                                print("[LESSON STATUS] Next button is enabled and displayed, countdown likely finished")
                                print(f"[LESSON STATUS] Clicking next button to proceed to next lesson at {datetime.datetime.now().strftime('%H:%M:%S')}")

                                # Click the next button
                                next_button.click()
                                time.sleep(3)  # Wait for page to load
                                print(f"[LESSON STATUS] Clicked next button, now at URL: {self.driver.current_url}")

                                # Check if the next lesson is already completed
                                if self._is_lesson_completed():
                                    print("[LESSON STATUS] Next lesson is already completed, clicking next again")
                                    self._click_next_button()

                                return True
                        except NoSuchElementException:
                            # Next button not found, continue waiting
                            print("[LESSON STATUS] Next button not found, continuing to wait")
                            pass
                    else:
                        # Check each countdown element
                        for element in countdown_elements:
                            try:
                                # Check if the countdown shows 0 or "Finished" or similar
                                element_text = element.text.strip().lower()
                                print(f"[LESSON STATUS] Countdown element text: '{element_text}'")

                                # Try to extract time values (minutes:seconds) from the text
                                import re
                                time_match = re.search(r'(\d+):(\d+)', element_text)
                                if time_match:
                                    minutes = int(time_match.group(1))
                                    seconds = int(time_match.group(2))
                                    total_seconds = minutes * 60 + seconds
                                    print(f"[LESSON STATUS] Extracted time: {minutes}:{seconds:02d} ({total_seconds} seconds remaining)")

                                # Check if timer is at or near zero
                                if "0:00" in element_text or "00:00" in element_text or "finished" in element_text or "complete" in element_text or (time_match and total_seconds <= 1):
                                    print(f"[LESSON STATUS] Countdown appears to be finished: '{element_text}'")
                                    print(f"[LESSON STATUS] Clicking next button to proceed to next lesson at {datetime.datetime.now().strftime('%H:%M:%S')}")

                                    # Try to find and click the next button
                                    try:
                                        next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                                        if next_button.is_enabled() and next_button.is_displayed():
                                            next_button.click()
                                            time.sleep(3)  # Wait for page to load
                                            print(f"[LESSON STATUS] Clicked next button, now at URL: {self.driver.current_url}")

                                            # Check if the next lesson is already completed
                                            if self._is_lesson_completed():
                                                print("[LESSON STATUS] Next lesson is already completed, clicking next again")
                                                self._click_next_button()
                                    except NoSuchElementException:
                                        print("[LESSON STATUS] Next button not found after countdown finished")
                                    except Exception as click_error:
                                        print(f"[LESSON STATUS] Error clicking next button: {click_error}")

                                    return True
                            except Exception as element_error:
                                print(f"[LESSON STATUS] Error checking countdown element text: {element_error}")
                                pass
                except NoSuchElementException:
                    # Countdown section not found, it might have been removed after completion
                    print("[LESSON STATUS] Countdown section not found, it might have been completed")

                    # Check if the next button is enabled
                    try:
                        next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                        if next_button.is_enabled() and next_button.is_displayed():
                            print("[LESSON STATUS] Next button is enabled and displayed, countdown likely finished")
                            print(f"[LESSON STATUS] Clicking next button to proceed to next lesson at {datetime.datetime.now().strftime('%H:%M:%S')}")

                            # Click the next button
                            next_button.click()
                            time.sleep(3)  # Wait for page to load
                            print(f"[LESSON STATUS] Clicked next button, now at URL: {self.driver.current_url}")

                            # Check if the next lesson is already completed
                            if self._is_lesson_completed():
                                print("[LESSON STATUS] Next lesson is already completed, clicking next again")
                                self._click_next_button()

                            return True
                    except NoSuchElementException:
                        # Next button not found, continue waiting
                        print("[LESSON STATUS] Next button not found, continuing to wait")
                        pass

            print("[LESSON STATUS] Maximum wait time reached")
            print(f"[LESSON STATUS] Attempting to click next button at {datetime.datetime.now().strftime('%H:%M:%S')}")

            # Try to find and click the next button
            try:
                next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                if next_button.is_enabled() and next_button.is_displayed():
                    # Log the action with timestamp
                    print(f"[LESSON STATUS] Found next button, clicking it at {datetime.datetime.now().strftime('%H:%M:%S')}")

                    # Take a screenshot before clicking (if possible)
                    try:
                        # Save screenshot directly in the project root directory
                        screenshot_path = f"next_button_screenshot_{int(time.time())}.png"
                        self.driver.save_screenshot(screenshot_path)
                        print(f"[LESSON STATUS] Saved screenshot before clicking next button: {screenshot_path}")
                    except Exception as ss_error:
                        print(f"[LESSON STATUS] Could not save screenshot: {ss_error}")
                        # Try with absolute path as fallback
                        try:
                            # Get the current working directory (absolute path)
                            current_dir = os.getcwd()
                            screenshot_path = os.path.join(current_dir, f"next_button_screenshot_{int(time.time())}.png")
                            self.driver.save_screenshot(screenshot_path)
                            print(f"[LESSON STATUS] Saved screenshot at absolute path: {screenshot_path}")
                        except Exception as fallback_error:
                            print(f"[LESSON STATUS] Could not save screenshot (fallback also failed): {fallback_error}")

                    # Click the next button
                    next_button.click()
                    time.sleep(3)  # Wait for page to load
                    print(f"[LESSON STATUS] Clicked next button after max wait time, now at URL: {self.driver.current_url}")

                    # Check if the next lesson is already completed
                    if self._is_lesson_completed():
                        print("[LESSON STATUS] Next lesson is already completed, clicking next again")
                        self._click_next_button()
                else:
                    print("[LESSON STATUS] Next button found but not enabled/displayed")
            except NoSuchElementException:
                print("[LESSON STATUS] Next button not found after max wait time")

                # Try alternative methods to find the next button
                try:
                    # Try using JavaScript to find and click the button
                    print("[LESSON STATUS] Trying to find next button using JavaScript")
                    self.driver.execute_script("document.getElementById('next-slide-button').click();")
                    time.sleep(3)
                    print(f"[LESSON STATUS] Clicked next button using JavaScript, now at URL: {self.driver.current_url}")
                except Exception as js_error:
                    print(f"[LESSON STATUS] JavaScript click failed: {js_error}")

                    # Try other selectors as a last resort
                    try:
                        print("[LESSON STATUS] Trying alternative selectors for next button")
                        alternative_selectors = [
                            "//button[contains(text(), 'Next')]",
                            "//a[contains(text(), 'Next')]",
                            "//button[contains(@class, 'next')]",
                            "//a[contains(@class, 'next')]"
                        ]

                        for selector in alternative_selectors:
                            try:
                                alt_button = self.driver.find_element(By.XPATH, selector)
                                if alt_button and alt_button.is_displayed():
                                    alt_button.click()
                                    time.sleep(3)
                                    print(f"[LESSON STATUS] Clicked alternative next button, now at URL: {self.driver.current_url}")
                                    break
                            except:
                                continue
                    except Exception as alt_error:
                        print(f"[LESSON STATUS] All alternative methods failed: {alt_error}")
            except Exception as click_error:
                print(f"[LESSON STATUS] Error clicking next button after max wait time: {click_error}")

            return True

        except Exception as e:
            print(f"[LESSON STATUS] Error during lesson completion wait: {e}")
            return False

    def _is_lesson_completed(self):
        """
        Check if the current lesson is already completed

        Returns:
            bool: True if the lesson is completed, False otherwise
        """
        try:
            # Look for completion indicators
            # This could be a progress bar, a checkmark, or text indicating completion
            completion_indicators = [
                "//*[contains(@class, 'completed') or contains(@class, 'done')]",
                "//span[contains(text(), '100%')]",
                "//div[contains(@class, 'progress-bar')][contains(@style, 'width: 100%')]"
            ]

            for indicator in completion_indicators:
                elements = self.driver.find_elements(By.XPATH, indicator)
                if elements:
                    print(f"[LESSON STATUS] Found completion indicator: {indicator}")
                    return True

            # Check if there's a countdown timer section
            try:
                # First try to find the section element using the XPath from the issue description
                section_element = self.driver.find_element(By.XPATH, "//*[@id=\"oe_structure_website_slides_lesson_top_1\"]/section")
                print("[LESSON STATUS] Found countdown section element in _is_lesson_completed")

                # Check if the countdown has ended by looking at the data-end-time attribute
                data_end_time = section_element.get_attribute("data-end-time")
                if data_end_time:
                    try:
                        end_time_float = float(data_end_time)
                        current_time = time.time()
                        if current_time >= end_time_float:
                            print(f"[LESSON STATUS] Countdown timer has ended (data-end-time: {data_end_time}, current time: {current_time})")
                            return True
                        else:
                            remaining_seconds = max(0, end_time_float - current_time)
                            minutes, seconds = divmod(int(remaining_seconds), 60)
                            print(f"[LESSON STATUS] Countdown timer still running: {minutes}:{seconds:02d} ({int(remaining_seconds)} seconds remaining)")
                            return False
                    except ValueError:
                        print(f"[LESSON STATUS] Could not convert data-end-time to float: {data_end_time}")

                # Then check for the div containing the canvas elements
                try:
                    countdown_section = section_element.find_element(By.XPATH, ".//div/div")
                    print("[LESSON STATUS] Found countdown canvas wrapper in _is_lesson_completed")

                    # Check if there are any canvas elements
                    canvas_elements = countdown_section.find_elements(By.TAG_NAME, "canvas")
                    if canvas_elements:
                        print(f"[LESSON STATUS] Found {len(canvas_elements)} canvas elements, lesson likely not completed yet")
                        return False
                except NoSuchElementException:
                    print("[LESSON STATUS] Could not find countdown canvas wrapper, lesson might be completed")

                # If we found the section but not the canvas elements, the lesson might be completed
                return True
            except NoSuchElementException:
                print("[LESSON STATUS] Could not find countdown section element, checking for next button")
                # If there's no countdown section, check if there's a next button
                # If there is, the lesson might be completed
                try:
                    next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
                    if next_button.is_enabled() and next_button.is_displayed():
                        print("[LESSON STATUS] Next button is enabled and displayed, lesson might be completed")
                        return True
                except NoSuchElementException:
                    print("[LESSON STATUS] Next button not found")
                    pass

            return False
        except Exception as e:
            print(f"[LESSON STATUS] Error checking if lesson is completed: {e}")
            return False

    def _click_next_button(self):
        """
        Click the next button to navigate to the next lesson

        Returns:
            str: URL of the next lesson, or None if there is no next button
        """
        try:
            # Use the specific XPath provided in the issue description
            next_button = self.driver.find_element(By.XPATH, "//*[@id=\"next-slide-button\"]")
            print("[LESSON STATUS] Found next button using the specific XPath")
            next_buttons = [next_button]
        except NoSuchElementException:
            print("[LESSON STATUS] Specific XPath for next button not found, trying alternatives...")
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
            print(f"[LESSON STATUS] Found next lesson button. URL: {next_url}")
            next_buttons[0].click()
            time.sleep(3)  # Wait for page to load
            current_url = self.driver.current_url
            print(f"[LESSON STATUS] Clicked next button, now at URL: {current_url}")
            return current_url
        else:
            print("[LESSON STATUS] No next lesson button found")
            return None

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
