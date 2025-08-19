from fastapi import FastAPI
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from passlib.hash import bcrypt
from database import SessionLocal, User
from schemas import ResearchRequest, ResearchResponse, LoginModel, SigninRequestModel, SigninResponseModel, LoginResponseModel
from memory import get_history
from pipeline import run_research_pipeline
from dotenv import load_dotenv
import os


load_dotenv()

google_api = os.getenv("GOOGLE_API_KEY")
# Create app instance
app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/research", response_model=ResearchResponse)
def generate_research(request: ResearchRequest):
    try:
        brief = run_research_pipeline(request)
        return brief.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/history/{conversation_id}")
def get_conversation_history(conversation_id: str):
    """Get all research briefs for a conversation"""
    try:
        history = get_history(conversation_id)
        return {
            "conversation_id": conversation_id,
            "brief_count": len(history),
            "briefs": [brief.model_dump() for brief in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@app.post('/signin', response_model=SigninResponseModel)
def signin(signinData: SigninRequestModel, db: Session = Depends(get_db)):

    user_exists = db.query(User).filter(User.email == signinData.email).first()

    if user_exists:
        raise HTTPException(status_code=400, detail="User already exist. Please kindly login")

    hash_password = bcrypt.hash(signinData.password)

    new_user = User(
        name=signinData.name,
        email=signinData.email,
        phone=signinData.phone,
        password=hash_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "status": "user registered successfully.",
        "name": signinData.name
    }


@app.post("/login", response_model=LoginResponseModel)
def login(loginData: LoginModel, db: Session = Depends(get_db)):
    get_email = db.query(User).filter(User.email == loginData.email).first()

    if not get_email:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    verify_pass = bcrypt.verify(loginData.password, get_email.password)
    if not verify_pass:
        print(f"Debug: {verify_pass}")
        raise HTTPException(status_code=400, detail="Invalid password")

    return {
        "status": True,
        "email": get_email.email
    }


@app.get("/")
def home():
    return {"message": "Research Assistant API is running!"}

