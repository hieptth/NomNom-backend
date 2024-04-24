from domain.models.foodModels import Food


class FoodService:
    def __init__(self, food_repository):
        self.food_repository = food_repository

    def add_food(self, name, description, tags):
        food = Food(food_id=None, name=name, description=description, tags=tags)
        self.food_repository.save(food)
        return food

    def get_food_by_id(self, food_id):
        return self.food_repository.find_by_id(food_id)

    def get_all_foods(self):
        return self.food_repository.find_all()

    def update_food(self, food_id, name, description, tags):
        food = self.get_food_by_id(food_id)
        if not food:
            raise ValueError("Food not found")
        food.name = name
        food.description = description
        food.tags = tags
        self.food_repository.save(food)
        return food

    def delete_food(self, food_id):
        food = self.get_food_by_id(food_id)
        if not food:
            raise ValueError("Food not found")
        self.food_repository.delete(food_id)
        return True