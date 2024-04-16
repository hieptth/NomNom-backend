import json

from supabase import create_client, Client
from itertools import groupby
import os
import pickle

from flask import Flask, request
from model.model import SearchModel

app = Flask(__name__)
try:
    SUPABASE_PROJECT_URL: str = "https://owqlwkvugpenhbianqia.supabase.co"
    SUPABASE_API_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93cWx3a3Z1Z3BlbmhiaWFucWlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxMDMzODkyMSwiZXhwIjoyMDI1OTE0OTIxfQ.Kpgtiz0Qmqrnjo17Ck-P7wVjSzjiPdXSN22WYoFDPjU"
except None:
    SUPABASE_PROJECT_URL: str = "default"
    SUPABASE_API_KEY: str = "default"

supabase: Client = create_client(
    SUPABASE_PROJECT_URL,
    SUPABASE_API_KEY,
)


@app.route('/')
def hello_world():  # put application's code here
    return 'nom nom nom'

# Deprecated buts keep for reference to create custom unpickler
# class CustomUnpickler(pickle.Unpickler):
#     def find_class(self, module, name):
#         if name == "SearchModel":
#             return SearchModel
#         return super().find_class(module, name)


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
