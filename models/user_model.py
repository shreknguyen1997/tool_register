class User:
    def __init__(self, username, password, url, hours=0, user_id=None, status="stopped", running_time=0):
        """
        Initialize a User object with login credentials and settings

        Args:
            username (str): The username for login
            password (str): The password for login
            url (str): The URL for the login page
            hours (int): Number of hours (default: 0)
            user_id (int, optional): The database ID of the user
            status (str): Current status of the user (running/stopped)
            running_time (int): How long the user has been running in seconds
        """
        self.username = username
        self.password = password
        self.url = url
        self.hours = hours
        self.id = user_id
        self.status = status
        self.running_time = running_time

    def __str__(self):
        """
        Return a string representation of the user

        Returns:
            str: String representation with username, URL, and hours
        """
        return f"{self.username} | {self.url} | {self.hours} hours"
