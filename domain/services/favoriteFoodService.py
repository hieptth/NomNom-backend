from domain.models.userModels import FavoriteFood


class FavoriteFoodService:
    def __init__(self, favorite_food_repository):
        self.favorite_food_repository = favorite_food_repository

    def get_favorite_foods_for_user(self, user_id):
        return self.favorite_food_repository.find_by_user_id(user_id)

    def add_to_favorites(self, user_id, food_id):
        favorite_food = FavoriteFood(favorite_id=None, user_id=user_id, food_id=food_id)
        self.favorite_food_repository.save(favorite_food)
        return favorite_food

    def remove_from_favorites(self, user_id, food_id):
        favorite_food = self.favorite_food_repository.find_by_user_id_and_food_id(user_id, food_id)
        if not favorite_food:
            raise ValueError("Favorite food not found")
        self.favorite_food_repository.delete(favorite_food.favorite_id)
        return True