from flask import Flask
from supabase import create_client, Client
import os

from flask import Flask, request


app = Flask(__name__)
SUPABASE_PROJECT_URL: str = os.getenv("SUPABASE_PROJECT_URL")
SUPABASE_API_KEY: str = os.getenv("SUPABASE_API_KEY")
supabase: Client = create_client(
    SUPABASE_PROJECT_URL,
    SUPABASE_API_KEY
)
@app.route('/')
def hello_world():  # put application's code here
    return 'Hello bruuuuuu'


if __name__ == '__main__':
    app.run()
