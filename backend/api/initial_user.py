from backend.api.database import SessionLocal
from backend.models.base import User
from backend.api.deps import bcrypt_context

def create_default_user():
    db = SessionLocal()
    try:
        # Check if the user already exists
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            hashed_password = bcrypt_context.hash("admin")
            default_user = User(username="admin", hashed_password=hashed_password, email="admin@example.com")
            db.add(default_user)
            db.commit()
            print("Default user created.")
        else:
            print("Default user already exists.")
    finally:
        db.close()
