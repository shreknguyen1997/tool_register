import sys
import os
from PyQt5.QtWidgets import QMessageBox
from models.user_model import User

class UserController:
    """
    Controller class for handling user-related operations
    """
    def __init__(self, db_model, view=None):
        """
        Initialize the UserController with a database model and optional view

        Args:
            db_model: The database model for data access
            view: The view for displaying messages (optional)
        """
        self.db_model = db_model
        self.view = view

    def get_all_users(self):
        """
        Get all users from the database

        Returns:
            list: List of User objects
        """
        return self.db_model.get_all_users()

    def search_users(self, search_term):
        """
        Search for users matching the search term

        Args:
            search_term (str): Term to search for

        Returns:
            list: List of matching User objects
        """
        return self.db_model.search_users(search_term)

    def add_user(self, username, password, url, hours, urls=None):
        """
        Add a new user to the database

        Args:
            username (str): Username
            password (str): Password
            url (str): Primary URL
            hours (int): Hours
            urls (list, optional): List of additional URLs

        Returns:
            tuple: (success, user_id, message)
        """
        # Validate input
        if not username or not password or not url:
            return False, None, "All fields except hours must be filled!"

        # Create user object
        new_user = User(username, password, url, hours, urls=urls)

        # Add to database
        user_id = self.db_model.add_user(new_user)

        if user_id:
            # Add additional URLs to the user_urls table
            if urls:
                for additional_url in urls:
                    if additional_url != url:  # Skip the primary URL as it's already in the users table
                        self.db_model.add_url_for_user(user_id, additional_url)

            return True, user_id, f"User {username} added successfully!"
        else:
            return False, None, "Failed to add user to database!"

    def update_user(self, user_id, username, password, url, hours, status="stopped", running_time=0, urls=None):
        """
        Update an existing user in the database

        Args:
            user_id (int): ID of the user to update
            username (str): Updated username
            password (str): Updated password
            url (str): Updated primary URL
            hours (int): Updated hours
            status (str): User status (running/stopped)
            running_time (int): How long the user has been running in seconds
            urls (list, optional): List of updated URLs

        Returns:
            tuple: (success, message)
        """
        # Validate input
        if not username or not password or not url:
            return False, "All fields except hours must be filled!"

        # Create updated user object
        updated_user = User(username, password, url, hours, user_id, status, running_time, urls=urls)

        # Update in database
        if self.db_model.update_user(user_id, updated_user):
            # Delete all existing URLs for this user
            self.db_model.delete_all_urls_for_user(user_id)

            # Add updated URLs to the user_urls table
            if urls:
                for additional_url in urls:
                    if additional_url != url:  # Skip the primary URL as it's already in the users table
                        self.db_model.add_url_for_user(user_id, additional_url)

            return True, f"User {username} updated successfully!"
        else:
            return False, "Failed to update user in database!"

    def delete_user(self, user_id):
        """
        Delete a user from the database

        Args:
            user_id (int): ID of the user to delete

        Returns:
            tuple: (success, message)
        """
        if self.db_model.delete_user(user_id):
            return True, "User deleted successfully!"
        else:
            return False, "Failed to delete user from database!"

    def delete_selected_users(self, user_ids):
        """
        Delete multiple users from the database

        Args:
            user_ids (list): List of user IDs to delete

        Returns:
            tuple: (success_count, total_count, message)
        """
        if not user_ids:
            return 0, 0, "No users selected for deletion!"

        success_count = 0
        for user_id in user_ids:
            if self.db_model.delete_user(user_id):
                success_count += 1

        if success_count > 0:
            if success_count < len(user_ids):
                return success_count, len(user_ids), f"Only {success_count} out of {len(user_ids)} users were deleted successfully."
            else:
                return success_count, len(user_ids), f"{success_count} users deleted successfully!"
        else:
            return 0, len(user_ids), "Failed to delete any users!"

    def close_connection(self):
        """Close the database connection"""
        if self.db_model:
            self.db_model.close()
