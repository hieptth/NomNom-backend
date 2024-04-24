class User:
    def __init__(self, user_id, name, email, hashed_password):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.hashed_password = hashed_password  # Consider storing hashed passwords only

class Comments:
    def __init__(self, comment_id, user_id, food_id, comment, created_at, parent_comment_id, has_child):
        self.comment_id = comment_id
        self.user_id = user_id
        self.food_id = food_id
        self.comment = comment
        self.created_at = created_at
        self.parent_comment_id = parent_comment_id
        self.has_child = has_child

class FavoriteFood:
    def __init__(self, user_id, food_id = None):
        self.user_id = user_id
        self.food_id = food_id or []

class UserRating:
    def __init__(self, rating_id, user_id, food_id, rating, created_at):
        self.rating_id = rating_id
        self.user_id = user_id
        self.food_id = food_id
        self.rating = rating  # Ensure this is within an acceptable range (e.g., 1-5)
        self.created_at = created_at

class SearchHistory:
    def __init__(self, search_id, user_id, food_id, timestamp):
        self.search_id = search_id
        self.user_id = user_id
        self.food_id = food_id
        self.timestamp = timestamp