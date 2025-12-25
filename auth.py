from pydantic import BaseModel

class User(BaseModel):
    username: str
    role: str

def authenticate_user(username, password):
    # Simple Mock Auth for Demo
    if username == "manager" and password == "admin123":
        return User(username="Manager", role="manager")
    elif username == "guest" and password == "guest123":
        return User(username="Guest", role="guest")
    return None