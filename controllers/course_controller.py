from models.course_model import Course

class CourseController:
    def __init__(self, db_model, parent=None):
        """
        Initialize the CourseController with a database model

        Args:
            db_model: The database model to use
            parent: The parent widget (optional)
        """
        self.db_model = db_model
        self.parent = parent

    def get_courses_for_user(self, user_id):
        """
        Get all courses for a specific user

        Args:
            user_id (int): ID of the user

        Returns:
            list: List of Course objects
        """
        return self.db_model.get_courses_for_user(user_id)

    def add_course(self, user_id, name, url, current_lesson="", completion_time=0, is_completed=0):
        """
        Add a new course

        Args:
            user_id (int): ID of the user who owns this course
            name (str): Name of the course
            url (str): URL of the course
            current_lesson (str, optional): URL or identifier of the current lesson
            completion_time (int, optional): Time to complete the course in hours
            is_completed (int, optional): Whether the course is completed (0=no, 1=yes)

        Returns:
            tuple: (success, message, course_id)
        """
        # Validate input
        if not name:
            return False, "Course name cannot be empty", None

        if not url:
            return False, "Course URL cannot be empty", None

        # Create a new Course object
        course = Course(user_id=user_id, name=name, url=url, current_lesson=current_lesson, 
                       completion_time=completion_time, is_completed=is_completed)

        # Add the course to the database
        course_id = self.db_model.add_course(course)

        if course_id:
            return True, "Course added successfully", course_id
        else:
            return False, "Failed to add course to database", None

    def update_course(self, course_id, name, url, current_lesson="", completion_time=None, is_completed=None):
        """
        Update an existing course

        Args:
            course_id (int): ID of the course to update
            name (str): New name of the course
            url (str): New URL of the course
            current_lesson (str, optional): New URL or identifier of the current lesson
            completion_time (int, optional): New time to complete the course in hours
            is_completed (int, optional): Whether the course is completed (0=no, 1=yes)

        Returns:
            tuple: (success, message)
        """
        # Validate input
        if not name:
            return False, "Course name cannot be empty"

        if not url:
            return False, "Course URL cannot be empty"

        # Get the existing course to preserve user_id
        courses = self.db_model.get_courses_for_user(None)  # This will get all courses
        course = next((c for c in courses if c.id == course_id), None)

        if not course:
            return False, "Course not found"

        # Update the course
        course.name = name
        course.url = url
        course.current_lesson = current_lesson
        if completion_time is not None:
            course.completion_time = completion_time
        if is_completed is not None:
            course.is_completed = is_completed

        # Update the course in the database
        success = self.db_model.update_course(course_id, course)

        if success:
            return True, "Course updated successfully"
        else:
            return False, "Failed to update course in database"

    def delete_course(self, course_id):
        """
        Delete a course

        Args:
            course_id (int): ID of the course to delete

        Returns:
            tuple: (success, message)
        """
        success = self.db_model.delete_course(course_id)

        if success:
            return True, "Course deleted successfully"
        else:
            return False, "Failed to delete course from database"

    def get_completion_ratio(self, user_id):
        """
        Calculate the completion ratio for a user's courses

        Args:
            user_id (int): ID of the user

        Returns:
            tuple: (completed_count, total_count, ratio_string)
        """
        courses = self.get_courses_for_user(user_id)

        if not courses:
            return 0, 0, "0/0"

        total_count = len(courses)
        completed_count = sum(1 for course in courses if course.is_completed)

        return completed_count, total_count, f"{completed_count}/{total_count}"
