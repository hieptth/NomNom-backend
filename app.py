import json

from supabase import create_client, Client
import os

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
     .select('food(*)').eq('user_id', 1).execute())
    return json.dumps(data)
# select f.*
# from user_likes_food ulf join food f on ulf.food_id = f.food_id
# where user_likes_food.user_id = 1

if __name__ == '__main__':
    app.run()
