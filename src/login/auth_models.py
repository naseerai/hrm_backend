from pydantic import BaseModel, ConfigDict, EmailStr
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int          # seconds
    refresh_token: str

class LoginRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # V2 requirement
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    user: dict
    access_token: str
    token_type: str
    expires_in: int          # seconds




