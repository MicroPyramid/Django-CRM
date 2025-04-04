# fastapi_app/schemas/user.py
from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True
