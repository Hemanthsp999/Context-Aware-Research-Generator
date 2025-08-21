# schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field, constr, EmailStr


class UserQuery(BaseModel):
    topic: constr(min_length=3)
    follow_up: bool = False
    conversation_id: Optional[str] = None  # lets API/CLI thread context
    user_id: Optional[str] = None


class Evidence(BaseModel):
    id: str
    title: str
    url: str
    snippet: Optional[str] = None


class ResearchBrief(BaseModel):
    topic: str
    context_used: Optional[str] = None
    summary: constr(min_length=20)
    key_findings: List[constr(min_length=3)]
    limitations: List[str] = []
    references: List[Evidence] = Field(default_factory=list)


class ResearchRequest(UserQuery):
    max_sources: int = 8


class ResearchResponse(ResearchBrief):
    pass


class SigninRequestModel(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str


class SigninResponseModel(BaseModel):
    status: str
    name: str


class LoginModel(BaseModel):
    email: EmailStr
    password: str


class LoginResponseModel(BaseModel):
    status: bool
    email: str

