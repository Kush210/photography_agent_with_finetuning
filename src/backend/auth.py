import bcrypt
import jwt
import datetime
import os
from google.cloud import firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firestore
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
#     "GOOGLE_APPLICATION_CREDENTIALS"
# )

db = firestore.Client(database="photo-agent-users")
users_collection = db.collection("users")

# Secret key for JWT
SECRET_KEY = os.getenv("JWT_SECRET", "mysecretkey")


# Hash Password
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# Verify Password
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


# Generate JWT Token
def generate_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(days=1),  # Token expires in 1 day
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# Authenticate User
def authenticate_user(email: str, password: str):
    user_doc = users_collection.document(email).get()
    if not user_doc.exists:
        return None
    user_data = user_doc.to_dict()
    if verify_password(password, user_data["password"]):
        return generate_token(email)
    return None
