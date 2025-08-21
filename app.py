from fastapi import FastAPI
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from passlib.hash import bcrypt
from datetime import datetime
from database import SessionLocal, User, Base, engine, Conversation, ResearchHistory
from schemas import ResearchRequest, ResearchResponse, LoginModel, SigninRequestModel, SigninResponseModel, LoginResponseModel
# from memory import get_history
from pipeline import run_research_pipeline
from dotenv import load_dotenv
import json
import os
Base.metadata.create_all(bind=engine)

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


@app.post("/{user_id}/research/", response_model=ResearchResponse)
def generate_research(user_id: int, request: ResearchRequest, db: Session = Depends(get_db)):
    try:
        # ✅ ensure user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # ✅ get or create conversation
        conversation = db.query(Conversation).filter(
            Conversation.conversation_id == request.conversation_id,
            Conversation.user_id == user.id
        ).first()

        if not conversation:
            conversation = Conversation(
                conversation_id=request.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
                user_id=user.id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # ✅ run pipeline
        brief = run_research_pipeline(request)

        # ✅ save into ResearchHistory
        new_history = ResearchHistory(
            topic=brief.topic,
            summary=brief.summary,
            sources=json.dumps([e.model_dump() for e in brief.references]),
            conversation_id=conversation.id
        )
        db.add(new_history)
        db.commit()

        return brief.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{user_id}/{conversation_id}/history")
def get_conversation_history(user_id: int, conversation_id: str, db: Session = Depends(get_db)):
    """Get all research briefs for a user's conversation"""
    try:
        # ✅ verify user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # ✅ get conversation
        conversation = db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found for this user")

        # ✅ get history
        history = db.query(ResearchHistory).filter(
            ResearchHistory.conversation_id == conversation.id
        ).all()

        return {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "brief_count": len(history),
            "briefs": [
                {
                    "topic": h.topic,
                    "summary": h.summary,
                    "sources": json.loads(h.sources) if h.sources else [],
                    "created_at": h.created_at
                }
                for h in history
            ]
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

