import json
from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
from datetime import datetime


from itertools import groupby
from dotenv import load_dotenv

load_dotenv()

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

# GET /foods?query=chicken&search_type=name&limit=10&offset=0
@app.route('/foods', methods=['GET'])
def search_foods():
    query = request.args.get('query')
    search_type = request.args.get('search_type')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    # Assuming a pre-defined function `search_foods` that interacts with Supabase
    result = supabase.table("food").select("*").ilike(search_type, f"%{query}%").limit(limit).offset(offset).execute()
    return jsonify(result.data), 200

# GET /foods/<food_id>

@app.route('/foods/<int:food_id>', methods=['GET'])
def get_food(food_id: int):
    food_result = supabase.table("food").select("*").eq("food_id", food_id).execute()
    if not food_result.data:
        return jsonify({"error": "Food not found"}), 404
    food = food_result.data[0]

    ratings_result = supabase.table("user_rates_food").select("rating").eq("food_id", food_id).execute()
    if ratings_result.data:
        ratings = [rating['rating'] for rating in ratings_result.data]
        food['average_rating'] = sum(ratings) / len(ratings)
    else:
        food['average_rating'] = None

    return jsonify(food), 200

# POST FAVORITE FOOD
@app.route('/my/foods', methods=['POST'])
def add_favorite_food():
    user_id = request.json.get('user_id')
    food_id = request.json.get('food_id')
    result = supabase.table('user_likes_food').insert({
    "user_id": user_id, 
    "food_id": food_id, 
    "created_at": datetime.now()
}).execute()
    if result.error:
        return jsonify({"error": str(result.error)}), 400
    return jsonify({"message": "Food added to favorites"}), 201

@app.route('/my/foods', methods=['GET'])
def get_favorite_foods():
    user_id = request.args.get('user_id', type=int)
    favorites_result = supabase.table('user_likes_food').select("food_id").eq("user_id", user_id).execute()
    if favorites_result.error:
        return jsonify({"error": str(favorites_result.error)}), 400
    return jsonify(favorites_result.data), 200

@app.route('/my/foods/<int:food_id>', methods=['DELETE'])
def delete_favorite_food(food_id: int):
    user_id = request.args.get('user_id', type=int)
    result = supabase.table('user_likes_food').delete().match({"user_id": user_id, "food_id": food_id}).execute()
    if result.error:
        return jsonify({"error": str(result.error)}), 400
    return jsonify({"message": "Food removed from favorites"}), 204




# POST /foods/<food_id>/comments
@app.route('/foods/<int:food_id>/comments', methods=['POST'])
def add_comment(food_id: int):
    user_id = request.json.get('user_id', type=int)
    comment = request.json.get('comment')
    parent_comment_id = request.json.get('parent_comment_id', None)

    # Start a transaction
    with supabase.transaction() as transaction:
        # Insert the new comment
        result = transaction.table('user_commentson_food').insert({
            "food_id": food_id,
            "user_id": user_id,
            "comment": comment,
            "parent_comment_id": parent_comment_id
        }).execute()

        # If this is a reply to another comment, update the parent comment's hasChild attribute
        if parent_comment_id is not None:
            update_result = transaction.table('user_commentson_food').update({"hasChild": True}).eq("comment_id", parent_comment_id).execute()
            if update_result.error:
                transaction.rollback()
                return jsonify({"error": "Failed to update parent comment", "details": str(update_result.error)}), 400

        # Check if the new comment was added successfully
        if result.error:
            transaction.rollback()
            return jsonify({"error": "Unable to add comment", "details": str(result.error)}), 400

    return jsonify({"message": "Comment added successfully"}), 201


# PUT /foods/<food_id>/comments/<comment_id>
@app.route('/foods/<int:food_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(food_id: int, comment_id: int):
    user_id = request.args.get('user_id', type=int)  # Assuming user_id is passed as query parameter for authentication
    result = supabase.table('user_commentson_food').delete().match({"user_id": user_id, "food_id": food_id, "comment_id": comment_id}).execute()

    if result.error:
        return jsonify({"error": "Unable to delete comment", "details": str(result.error)}), 400
    return jsonify({"message": "Comment deleted successfully"}), 204


# POST /foods/<food_id>/ratings
@app.route('/foods/<int:food_id>/ratings', methods=['POST'])
def add_rating(food_id: int):
    user_id = request.json.get('user_id', type=int)
    rating = request.json.get('rating', type=int)

    # Insert the rating into the 'user_rates_food' table
    result = supabase.table('user_rates_food').insert({
        "food_id": food_id,
        "user_id": user_id,
        "rating": rating
    }).execute()

    if result.error:
        return jsonify({"error": "Unable to add rating", "details": str(result.error)}), 400
    return jsonify({"message": "Rating added successfully"}), 201


# PUT /foods/<food_id>/ratings/<rating_id>
@app.route('/foods/<int:food_id>/ratings/<int:rating_id>', methods=['PUT'])
def update_rating(food_id: int, rating_id: int):
    user_id = request.json.get('user_id', type=int)
    new_rating = request.json.get('rating', type=int)

    # Update the rating in the 'user_rates_food' table
    result = supabase.table('user_rates_food').update({
        "rating": new_rating
    }).match({"user_id": user_id, "food_id": food_id, "rating_id": rating_id}).execute()

    if result.error:
        return jsonify({"error": "Unable to update rating", "details": str(result.error)}), 400
    return jsonify({"message": "Rating updated successfully"}), 200



if __name__ == '__main__':
    app.run(debug=True ,host='0.0.0.0', port=5001)


