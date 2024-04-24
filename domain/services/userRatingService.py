from domain.models.userModels import UserRating


class UserRatingService:
    def __init__(self, user_rating_repository):
        self.user_rating_repository = user_rating_repository
        
    def get_all_ratings(self):
        return self.user_rating_repository.find_all()

    def get_all_ratings_for_user(self, user_id):
        return self.user_rating_repository.find_all_by_user_id(user_id)

    def get_all_ratings_for_food(self, food_id):
        return self.user_rating_repository.find_all_by_food_id(food_id)
    
    def get_user_rating_by_id(self, rating_id):
        return self.user_rating_repository.find_by_id(rating_id)

    def rate_food(self, user_id, food_id, rating):
        user_rating = UserRating(rating_id=None, user_id=user_id, food_id=food_id, rating=rating)
        self.user_rating_repository.save(user_rating)
        return user_rating

    def update_rating(self, rating_id, new_rating):
        user_rating = self.get_user_rating_by_id(rating_id)
        if not user_rating:
            raise ValueError("User rating not found")
        user_rating.rating = new_rating
        self.user_rating_repository.save(user_rating)
        return user_rating

    def delete_rating(self, rating_id):
        rating = self.get_user_rating_by_id(rating_id)
        if not rating:
            raise ValueError("Rating not found")
        self.user_rating_repository.delete(rating_id)
        return True