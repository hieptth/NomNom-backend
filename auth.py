import os
from flask import app, current_app, Blueprint, request, jsonify, redirect
from gotrue.errors import AuthApiError

auth = Blueprint("auth", __name__, url_prefix="/auth")
with app.app_context():
    supabase = current_app.config['SUPABASE_CLIENT']

@auth.route("/signin", methods=["POST"])
def signin():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = supabase.auth.sign_in_with_password(
            credentials={"email": email, "password": password}
        )
        if user:
            return jsonify({"message": "Login successful", "user": user}), 200
    except AuthApiError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"error": "Login failed"}), 401

@auth.route("/signin/google")
def signin_with_google():
    redirect_url = f"{request.host_url}auth/callback"
    resp = supabase.auth.sign_in_with_oauth(
        {
            "provider": "google",
            "options": {"redirect_to": redirect_url},
        }
    )
    return redirect(resp.url)

@auth.route("/signin/apple")
def signin_with_apple():
    redirect_url = f"{request.host_url}auth/callback"
    resp = supabase.auth.sign_in_with_oauth(
        {
            "provider": "apple",
            "options": {"redirect_to": redirect_url},
        }
    )
    return redirect(resp.url)

@auth.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = supabase.auth.sign_up(
            email=email,
            password=password
        )
        if user:
            return jsonify({"message": "Registration successful", "user": user}), 200
    except AuthApiError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"error": "Registration failed"}), 401


@auth.route("/signout", methods=["POST"])
def signout():
    try:
        # Assuming the access token is sent in the Authorization header
        access_token = request.headers.get("Authorization").split(" ")[1]
        supabase.auth.sign_out(access_token)
        return jsonify({"message": "Logout successful"}), 200
    except AuthApiError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth.route("/callback")
def callback():
    # This route should handle the OAuth callback and process the user's information.
    # You might need to set up a session or return a token to the user here.
    # The implementation will depend on your frontend and how it handles the OAuth flow.
    return jsonify({"message": "OAuth callback endpoint. Implement as needed."})
