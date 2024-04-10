from model.model import SearchModel
import pickle
from typing import List

model:SearchModel = pickle.load(open('model/model0604.pkl', 'rb'))
def infer_similar_foods(food_history: List[dict]):
    for food in food_history:
        similar_foods = model.search(
            name=food["name"],
            tags=", ".join(food["tags"]),
            nutrition=[600, 80, 10, 50, 150, 30, 50],
            # NUTRITIONS = ['calories', 'fat', 'sugar', 'sodium', 'protein', 'saturated_fat', 'carbohydrates']
        )[:10]  # Take 10 most similar (can take up to k)
        names = [similar_food[0]['name'] for similar_food in similar_foods]
        ids = [similar_food[0]['id'] for similar_food in similar_foods]
        print(names)
        print(ids)
