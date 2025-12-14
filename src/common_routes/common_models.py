from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    office_mail: str | None = None
    role: str | None = None
    mobile: str | None = None
    created_by: str | None = None

class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    role: str | None = None
    mobile: str | None = None


class ChangePasswordRequest(BaseModel):
    user_id: str
    new_password: str