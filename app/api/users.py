from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas.userpayload import UserCreate, UserResponse

router = APIRouter()

# Create a new user
@router.post("/")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
    )
    db.add(user)
    db.commit()
    return {
        "message": "User created successfully",
        "user_id": user.id,
        "user_name": user.name,
        "user_email": user.email,
    }