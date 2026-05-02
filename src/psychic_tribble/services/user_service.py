# src/psychic_tribble/services/user_service.py

class UserService:
    """
    Encapsulates all user-related operations:
    - create_user
    - get_user
    - update_user
    - delete_user
    """

    def __init__(self, repository):
        self.repository = repository

    def create_user(self, user_data: dict):
        """
        Registers a new user and initializes default calendar settings.
        """
        # Enhancement: Define default settings for new users
        defaults = {
            "timezone": "UTC",
            "theme": "dark",
            "notifications_enabled": True
        }
        
        # Merge defaults with provided user_data
        final_data = {**defaults, **user_data}
        
        if "email" not in final_data:
            raise ValueError("Email is required to create a user.")
            
        return self.repository.add(final_data)

    def get_user(self, user_id: str):
        """
        Retrieves user profile and settings.
        """
        user = self.repository.get_by_id(user_id)
        if not user:
            return None
        return user

    def update_user(self, user_id: str, updates: dict):
        """
        Updates user preferences or profile information.
        """
        # Ensure we aren't overwriting the unique identifier
        updates.pop("id", None)
        
        return self.repository.update(user_id, updates)

    def delete_user(self, user_id: str):
        """
        Deletes the user and should trigger a cleanup of their tasks/events.
        """
        # Enhancement: In a real app, you'd trigger a 'cascade delete' 
        # to remove their calendar events too.
        return self.repository.delete(user_id)

    # --- Added Enhancement: Preference Management ---

    def get_user_timezone(self, user_id: str):
        """
        Helper to quickly get a user's timezone for calendar calculations.
        """
        user = self.get_user(user_id)
        return user.get("timezone", "UTC") if user else "UTC"
