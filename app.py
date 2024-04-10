import json

from supabase import create_client, Client
from itertools import groupby
import os

import pickle

from flask import Flask, request

app = Flask(__name__)
try:
    SUPABASE_PROJECT_URL: str = os.getenv("SUPABASE_PROJECT_URL")
    SUPABASE_API_KEY: str = os.getenv("SUPABASE_API_KEY")
except None:
    SUPABASE_PROJECT_URL: str = "default"
    SUPABASE_API_KEY: str = "default"

supabase: Client = create_client(
    SUPABASE_PROJECT_URL,
    SUPABASE_API_KEY,
)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello bruuuuuu'

from model.model import SearchModel
with open('/recommendation/model/model0604.pkl', 'rb') as f:
    model: SearchModel = pickle.load(f)

@app.route('/recommendations/<user_id>', methods=["GET"])
def get_recommendations(user_id:int):
    # Fetch all user's search history
    (_, response_data), _ = supabase.table('user_searches_food').select('food(food_id)').eq('user_id', user_id).execute()
    # food id -> tags
    # response_data: List of food json objects
    food_ids = [food_object['food']['food_id'] for food_object in response_data]
    (_, response_data), _ = supabase.table('food_tag').select('food(*), tag(*)').in_('food_id', food_ids).execute()
    # TODO: Implement a way to get the tags from the food_id
    grouped_by_response = groupby(response_data, lambda x: x['food'])
    food_history = []
    for food, tags in grouped_by_response:
        tag_list = list(tags)
        food['tags'] = list(map(lambda x: x['tag']['content'], tag_list))
        food_history.append(food)
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
    return json.dumps(food_history)

@app.route('/foods/<food_id>', methods=["GET"])
def get_food(food_id:int):
    print(food_id)
    data, _ = supabase.table('food').select('*').eq('food_id', food_id).execute()
    print(f"Data {data}")
    return data[1][0]
    # 1 for the actual json list is in the second object
    # 0 for the json is the only element in json list

@app.route('/my/foods', methods=["POST"])
def add_favorite_food():
    request_body = request.get_json()
    favorite_food_id = request_body['food_id']
    # Save to database
    # Not yet implemented logged-in user, so default to user_id = 1
    data, _ = supabase.table('user_likes_food').insert({
        'user_id': 2,
        'food_id': favorite_food_id
    }).execute()
    return json.dumps({
        "status": "201",
        "message": "Successfully added to favorites"
    })

@app.route('/my/foods', methods=["GET"])
def get_favorite_foods():
    data, _ = (supabase.table('user_likes_food')
     .select('food(*)').eq('user_id', 2).execute())
    return json.dumps(data)
# select f.*
# from user_likes_food ulf join food f on ulf.food_id = f.food_id
# where user_likes_food.user_id = 1

if __name__ == '__main__':
    app.run()
