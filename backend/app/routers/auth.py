"""Auth: register / login / me.

First admin: registering with role=admin is allowed only while no admin
exists yet. After that, only an existing admin can create another admin.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import User, UserRole
from ..schemas import LoginRequest, Token, UserCreate, UserOut
from ..security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    role = data.role
    if role == UserRole.ADMIN and db.query(User).filter(User.role == UserRole.ADMIN).first():
        raise HTTPException(status_code=403, detail="Admin already exists; ask an admin to create more admins")
    user = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        hashed_password=get_password_hash(data.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return Token(access_token=create_access_token({"sub": str(user.id), "role": user.role.value}))


@router.post("/login-json", response_model=Token)
def login_json(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return Token(access_token=create_access_token({"sub": str(user.id), "role": user.role.value}))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
