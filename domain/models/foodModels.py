class Food:
    def __init__(self, food_id, name, description, average_rating, calories, total_fat, saturated_fat, carbohydrates, protein, pictures = None):
        self.food_id = food_id
        self.name = name
        self.description = description
        self.average_rating = average_rating
        self.calories = calories
        self.total_fat = total_fat
        self.sugar = sugar
        self.sodium = sodium
        self.protein = protein
        self.saturated_fat = saturated_fat
        self.carbohydrates = carbohydrates
        self.pictures = pictures or []

class FoodPicture:
    def __init__(self, picture_id, food_id, picture_url):
        self.picture_id = picture_id
        self.food_id = food_id
        self.picture_url = picture_url

class Tag:
    def __init__(self, tag_id, content):
        self.tag_id = tag_id
        self.content = content