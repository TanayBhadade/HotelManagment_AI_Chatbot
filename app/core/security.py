from passlib.context import CryptContext
from datetime import datetime, timedelta
# In real auth, you'd use python-jose for JWT tokens here

# Setup Password Hashing (Bcrypt is standard)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)