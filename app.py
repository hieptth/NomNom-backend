import json
import time
import jwt
from flask import Flask, request, jsonify
from datetime import datetime
from supabase import create_client, Client
from gotrue.errors import AuthApiError
import os
from datetime import datetime
from postgrest.exceptions import APIError
import requests

from itertools import groupby
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

try:
    SUPABASE_PROJECT_URL: str = os.getenv("SUPABASE_PROJECT_URL")
    SUPABASE_API_KEY: str = os.getenv("SUPABASE_API_KEY")
except Exception as e:
    app.logger.error(f"Error loading environment variables: {str(e)}")
    SUPABASE_PROJECT_URL = "default"
    SUPABASE_API_KEY = "default"

supabase: Client = create_client(
    SUPABASE_PROJECT_URL,
    SUPABASE_API_KEY,
)

def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            token = token.split(" ")[1]
            app.logger.debug(f"Token received: {token}")
            data = jwt.decode(token, jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
            app.logger.debug(f"Token decoded: {data}")
            if (data["exp"] < time.time()):
                raise jwt.ExpiredSignatureError
            current_user = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'message': 'Token is invalid: ' + str(e)}), 401

        return f(current_user, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/iam/signin', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    try:
        response = supabase.auth.sign_in_with_password(credentials={"email": email, "password": password})

        if not response.user:
            return jsonify({"error": "Login failed"}), 401
        else:
            return jsonify({
                'user': response.user.email,
                'session': response.session.access_token
            }), 200
    except Exception as message:
        return jsonify({"error": str(message)}), 500

@app.route('/iam/signup', methods=['POST'])
def register():
    email = request.json['email']
    password = request.json['password']
    try:
        response = supabase.auth.sign_up(credentials={"email": email, "password": password})

        if not response.user:
            return jsonify({"error": response.error.message}), 400
        else:
            return jsonify({
                'user': response.user.email,
                'session': response.session.access_token
            }), 200
    except Exception as message:
        return jsonify({"error": str(message)}), 500

@app.route('/iam/signout', methods=['POST'])
@token_required
def logout():
    token = request.headers.get('Authorization').split(" ")[1]
    try:
        response = supabase.auth.sign_out(token)
        app.logger.debug(f"Logout response: {response}")

        if response is None:
            app.logger.error("Logout failed: No response from Supabase")
            return jsonify({"error": "Logout failed due to no response from Supabase"}), 500

        if response.error:
            app.logger.debug(f"Error during logout: {response.error}")
            return jsonify({"error": response.error.message}), 400

        return jsonify({"message": "Successfully logged out"}), 200
    except Exception as e:
        app.logger.error(f"Exception during logout: {str(e)}")
        return jsonify({"error": str(e)}), 500


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
    # Get recommendations from the recommendation engine
    resp = requests.post(
        #TODO: Follow these steps to get the ngrok link to the recommendation engine
        # Step 1: Access the Colab environment: https://colab.research.google.com/drive/1Ez60gkN1aIp2eNZh9aHMul9kZEtTyGKU?fbclid=IwAR2xqWVkDtC1gRZkYnOsQEIoGTZtcVovhcdcb7vPdJjVLja6vQdLmnjQTUk&authuser=1#scrollTo=SCgfvhLVipAQ
        # Step 2: In the menu bar, click "Runtime" -> "Run all". Wait until it stops at the "assert False" cell.
        # Step 3: Find the "Deploy the NomNom" cell, run it and its subsequent cells.
        # Step 4: Scrolling down, you should be seeing the ngrok link to the recommendation engine
        # Step 5: Copy the link and paste it here
        "https://ab22-34-73-82-0.ngrok-free.app/recommend",
        json={"food_history": food_history}
    )
    food_indices = list(resp.json())
    print(food_indices)
    # Get the food objects from the indices
    recommendation_resp = supabase.table('food').select('*').in_('food_id', food_indices).execute()

    return jsonify(recommendation_resp.data)
# # GET /foods?query=chicken&search_type=name&limit=10&offset=0
# @app.route('/foods', methods=['GET'])
# @token_required
# def search_foods():
#     query = request.args.get('query')
#     search_type = request.args.get('search_type')
#     limit = int(request.args.get('limit', 10))
#     offset = int(request.args.get('offset', 0))

#     # Assuming a pre-defined function `search_foods` that interacts with Supabase
#     result = supabase.table("food").select("*").ilike(search_type, f"%{query}%").limit(limit).offset(offset).execute()
#     return jsonify(result.data), 200



# GET food information

@app.route('/foods/<int:food_id>', methods=['GET'])
# @token_required
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


# POST Favorite food
@app.route('/my/foods', methods=['POST'])
# @token_required
def add_favorite_food():

    try:
        user_id = request.json.get('user_id')
        food_id = request.json.get('food_id')
        # Check if the user_id exists in the 'user' table
        user_check = supabase.table('user').select('user_id').eq('user_id', user_id).execute()
        if user_check.data is None or len(user_check.data) == 0:
            return jsonify({"error": "User not found"}), 404

        # Check if the food_id exists
        food_check = supabase.table('food').select('food_id').eq('food_id', food_id).execute()
        if food_check.data is None or len(food_check.data) == 0:
            return jsonify({"error": "Food item not found or query failed"}), 404

        # Check if the favorite food has already been added
        favorite_check = supabase.table('user_likes_food').select('*').eq('user_id', user_id).eq('food_id', food_id).execute()
        if favorite_check.data and len(favorite_check.data) > 0:
            return jsonify({"error": "Food already marked as favorite"}), 409

        # Format datetime to ISO 8601 string
        created_at = datetime.now().isoformat()
        print("Debug: created_at ISO format", created_at)  # Debug statement

        # Insert data into 'user_likes_food' table
        result = supabase.table('user_likes_food').insert({
            "user_id": user_id,
            "food_id": food_id,
            "created_at": created_at
        }).execute()



        return jsonify({"message": "Food added to favorites"}), 201
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500



@app.route('/my/foods/<int:user_id>', methods=['GET'])
# @token_required
def get_favorite_foods(user_id: int):

    try:
        favorites_result = supabase.table('user_likes_food').select("food_id").eq("user_id", user_id).execute()
        return jsonify(favorites_result.data), 200
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500


@app.route('/my/foods/<int:user_id>/<int:food_id>', methods=['DELETE'])# @token_required
def delete_favorite_food(user_id, food_id):
    try:
        # Targeting the specific record with both user_id and food_id
        find = supabase.table('user_likes_food').select('*').eq('user_id', user_id).eq('food_id', food_id).execute()
        if not find.data:
            return jsonify({"error": "Food item not found"}), 404
        result = supabase.table('user_likes_food').delete().eq('user_id', user_id).eq('food_id', food_id).execute()
        return jsonify({"message":"Food removed from favorites"}), 204
    except APIError as e:
        # Handling APIError specifically from Supabase/PostgREST
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500
    except Exception as e:
        # General exception handling
        return jsonify({'error': str(e)}), 500



##################COMMENT SECTION####################

# POST /foods/<food_id>/comments
@app.route('/foods/comments/<int:food_id>', methods=['POST'])
# @token_required
def add_comment(food_id: int):
    try:
        user_id = request.json.get('user_id')
        comment = request.json.get('comment')
        parent_comment_id = request.json.get('parent_comment_id', None)

        result = supabase.table('user_commentson_food').insert({
                "food_id": food_id,
                "user_id": user_id,
                "comment": comment,
                "parent_comment_id": parent_comment_id
            }).execute()

        return jsonify({"message": "Comment added successfully"}), 201
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500

# GET /foods/comments/<food_id>
@app.route('/foods/comments/<int:food_id>', methods=['GET'])
def get_comments(food_id: int):
    try:
        result = supabase.table('user_commentson_food').select('*').eq('food_id', food_id).execute()
        return jsonify(result.data), 200
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500

# Delete comment /foods/comments/<user_id>/<food_id>/<comment_id>
@app.route('/foods/comments/<int:user_id>/<int:food_id>/<int:comment_id>', methods=['DELETE'])
def delete_comment(user_id: int,food_id: int, comment_id: int):
    try:
        find = supabase.table('user_commentson_food').select('*').match({"user_id": user_id, "food_id": food_id, "comment_id": comment_id}).execute()
        if not find.data:
            return jsonify({"error": "Comment not found"}), 404

        result = supabase.table('user_commentson_food').delete().match({ "user_id": user_id,"food_id": food_id, "comment_id": comment_id}).execute()

        return jsonify({"message": "Comment deleted successfully"}), 204
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500

# PUT /foods/comments/<user_id>/<food_id>/<comment_id>
@app.route('/foods/comments/<int:user_id>/<int:food_id>/<int:comment_id>', methods=['PUT'])
def update_comment(user_id: int, food_id: int, comment_id: int):
    try:
        comment = request.json.get('comment')
        find = supabase.table('user_commentson_food').select('*').match({"user_id": user_id, "food_id": food_id, "comment_id": comment_id}).execute()
        if not find.data:
            return jsonify({"error": "Comment not found"}), 404
        result = supabase.table('user_commentson_food').update({
            "comment": comment
        }).match({"user_id": user_id, "food_id": food_id, "comment_id": comment_id}).execute()
        return jsonify({"message": "Comment updated successfully"}), 200
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500

####################RATING SECTION####################

# POST /foods/ratings/<food_id>
@app.route('/foods/ratings/<int:food_id>', methods=['POST'])
# @token_required
def add_rating(food_id: int):
    try:
        user_id = request.json.get('user_id')
        rating = request.json.get('rating')

        # Insert the rating into the 'user_rates_food' table
        result = supabase.table('user_rates_food').insert({
            "food_id": food_id,
            "user_id": user_id,
            "rating": rating
        }).execute()


        return jsonify({"message": "Rating added successfully"}), 201
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500


# PUT /foods/ratings/<food_id>/<rating_id>
@app.route('/foods/ratings/<int:food_id>/<int:rating_id>', methods=['PUT'])
def update_rating(food_id: int, rating_id: int):
    try:
        rating = request.json.get('rating')
        find = supabase.table('user_rates_food').select('*').match({"food_id": food_id, "rating_id": rating_id}).execute()
        if not find.data:
            return jsonify({"error": "Rating not found"}), 404
        result = supabase.table('user_rates_food').update({
            "rating": rating
        }).match({"food_id": food_id, "rating_id": rating_id}).execute()
        return jsonify({"message": "Rating updated successfully"}), 200
    except APIError as e:
        error_message = e.args[0] if e.args else "Unknown database error"
        return jsonify({'error': error_message}), 500



if __name__ == '__main__':
    app.run(debug=True ,host='0.0.0.0', port=5001)


