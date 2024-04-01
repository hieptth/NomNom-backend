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
    SUPABASE_API_KEY
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


if __name__ == '__main__':
    app.run()
