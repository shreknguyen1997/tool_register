class Course:
    def __init__(self, user_id, name, url, current_lesson="", last_accessed=None, course_id=None, completion_time=0, is_completed=0):
        """
        Initialize a Course object with course details

        Args:
            user_id (int): The ID of the user who owns this course
            name (str): The name of the course
            url (str): The URL of the course
            current_lesson (str, optional): The URL or identifier of the current lesson
            last_accessed (datetime, optional): When the course was last accessed
            course_id (int, optional): The database ID of the course
            completion_time (int, optional): The time to complete the course in hours
            is_completed (int, optional): Whether the course is completed (0=no, 1=yes)
        """
        self.user_id = user_id
        self.name = name
        self.url = url
        self.current_lesson = current_lesson
        self.last_accessed = last_accessed
        self.id = course_id
        self.completion_time = completion_time
        self.is_completed = is_completed

    def __str__(self):
        """
        Return a string representation of the course

        Returns:
            str: String representation with name and URL
        """
        return f"{self.name} | {self.url}"
