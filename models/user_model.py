class User:
    def __init__(self, username, password, url, hours=0, user_id=None, status="stopped", running_time=0, urls=None):
        """
        Initialize a User object with login credentials and settings

        Args:
            username (str): The username for login
            password (str): The password for login
            url (str): The primary URL for the login page (for backward compatibility)
            hours (int): Number of hours (default: 0)
            user_id (int, optional): The database ID of the user
            status (str): Current status of the user (running/stopped)
            running_time (int): How long the user has been running in seconds
            urls (list, optional): List of dictionaries with 'url' and 'hours' keys
        """
        self.username = username
        self.password = password
        self.url = url  # Keep for backward compatibility
        self.hours = hours
        self.id = user_id
        self.status = status
        self.running_time = running_time
        self.urls = urls or []

        # Convert any string URLs to dictionaries
        for i, url_item in enumerate(self.urls):
            if isinstance(url_item, str):
                self.urls[i] = {'url': url_item, 'hours': 0}
            elif isinstance(url_item, dict) and 'hours' not in url_item:
                url_item['hours'] = 0

        # Do not automatically add the primary URL to the study URLs list
        # The primary URL is for login, while the URLs list is for study materials

    def __str__(self):
        """
        Return a string representation of the user

        Returns:
            str: String representation with username, primary URL, and hours
        """
        return f"{self.username} | {self.url} | {self.hours} hours"

    def add_url(self, url, hours=0):
        """
        Add a URL to the user's list of URLs if it's not already there

        Args:
            url (str): URL to add
            hours (int): Number of hours for this URL (default: 0)
        """
        # Check if the URL is already in the list
        url_exists = False
        for url_item in self.urls:
            if isinstance(url_item, dict) and url_item.get('url') == url:
                url_exists = True
                break
            elif isinstance(url_item, str) and url_item == url:
                url_exists = True
                break

        if url and not url_exists:
            self.urls.append({'url': url, 'hours': hours})

    def remove_url(self, url):
        """
        Remove a URL from the user's list of URLs

        Args:
            url (str): URL to remove or dictionary with 'url' key
        """
        # Find the URL in the list
        url_to_remove = None
        for i, url_item in enumerate(self.urls):
            if isinstance(url_item, dict) and url_item.get('url') == url:
                url_to_remove = i
                break
            elif isinstance(url_item, str) and url_item == url:
                url_to_remove = i
                break

        # Remove the URL if found
        if url_to_remove is not None:
            removed_url = self.urls.pop(url_to_remove)

            # If we removed the primary URL, update it to the first available URL or empty string
            if isinstance(removed_url, dict) and removed_url.get('url') == self.url:
                self.url = self.urls[0].get('url') if self.urls else ""
            elif isinstance(removed_url, str) and removed_url == self.url:
                self.url = self.urls[0].get('url') if self.urls else ""
