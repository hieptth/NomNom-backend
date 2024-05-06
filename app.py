import json
import time
import jwt
from flask import Flask, request, jsonify
from supabase import create_client, Client
from gotrue.errors import AuthApiError
import os

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
@token_required
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


@app.route('/foods', methods=['GET'])
@token_required
def search_foods():
    query = request.args.get('query')
    search_type = request.args.get('search_type')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    # Search logic to fetch foods based on query and search_type
    # This is a simplified example assuming a function `search_foods` exists
    foods = search_foods(query, search_type, limit, offset)
    return jsonify(foods)

@app.route('/foods/<int:food_id>', methods=['GET'])
@token_required
def get_food(food_id):
    # Fetch the food details
    food_result = supabase.table("foods").select("*").eq("food_id", food_id).execute()

    if not food_result.data:
        return jsonify({"error": "Food not found"}), 404

    food = food_result.data[0]

    # Calculate the average rating for the food
    ratings_result = supabase.table("ratings").select("rating").eq("food_id", food_id).execute()

    if ratings_result.data:
        # Extract ratings and compute the average
        ratings = [rating['rating'] for rating in ratings_result.data]
        average_rating = sum(ratings) / len(ratings)
        food['average_rating'] = average_rating
    else:
        # If there are no ratings, set the average rating to None or a default value
        food['average_rating'] = None

    return jsonify(food)

@app.route('/my/foods', methods=['POST'])
@token_required
def add_favorite_food():
    user_id = 1  # This should be obtained from session or token
    food_id = request.json.get('food_id')
    result = supabase.table('favorites').insert({"user_id": user_id, "food_id": food_id}).execute()
    return jsonify({"message": "Food added to favorites"}), 201

@app.route('/my/foods', methods=['GET'])
@token_required
def get_favorite_foods():
    user_id = 1  # This should be obtained from session or token
    favorites = supabase.table('favorites').select("food_id").eq("user_id", user_id).execute()
    return jsonify(favorites.data)

@app.route('/my/foods/<int:food_id>', methods=['DELETE'])
@token_required
def delete_favorite_food(food_id):
    user_id = 1  # This should be obtained from session or token
    result = supabase.table('favorites').delete().match({"user_id": user_id, "food_id": food_id}).execute()
    return jsonify({"message": "Food removed from favorites"}), 204

@app.route('/user/comments', methods=['POST'])
@token_required
def add_comment():
    user_id = request.json.get('user_id')
    food_id = request.json.get('food_id')
    comment = request.json.get('comment')

    # Tùy chọn: Kiểm tra parent_comment_id, nếu có trong request
    parent_comment_id = request.json.get('parent_comment_id', None)

    # Thực hiện chèn bình luận vào cơ sở dữ liệu
    result = supabase.table('comments').insert({
        "food_id": food_id,
        "user_id": user_id,
        "comment": comment,
        "parent_comment_id": parent_comment_id
    }).execute()

    # Kiểm tra kết quả và trả về phản hồi phù hợp
    if result.error:
        return jsonify({"error": "Unable to add comment", "details": str(result.error)}), 400
    return jsonify({"message": "Comment added successfully"}), 201


@app.route('/user/ratings', methods=['POST'])
@token_required
def add_rating():
    user_id = request.json.get('user_id')
    food_id = request.json.get('food_id')
    rating = request.json.get('rating')

    # Thực hiện chèn đánh giá vào cơ sở dữ liệu
    result = supabase.table('ratings').insert({
        "food_id": food_id,
        "user_id": user_id,
        "rating": rating
    }).execute()

    # Kiểm tra kết quả và trả về phản hồi phù hợp
    if result.error:
        return jsonify({"error": "Unable to add rating", "details": str(result.error)}), 400
    return jsonify({"message": "Rating added successfully"}), 201


if __name__ == '__main__':
    app.run(debug=True ,host='0.0.0.0', port=5001)

