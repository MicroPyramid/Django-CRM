# fastapi_app/routers/users.py
from fastapi import APIRouter
from common.models import User  # Django model

router = APIRouter()

@router.get("/")
def list_users():
    return [{"id": user.id, "email": user.email} for user in User.objects.all()]
