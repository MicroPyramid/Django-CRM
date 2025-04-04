# fastapi_app/routers/users.py
from common.models import User  # Django model
import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import BaseUserManager
router = APIRouter()

class SocialLoginSerializer(BaseModel):
    token: str

@router.post("/google", summary="Login through Google")
def google_login(payload: SocialLoginSerializer, request: Request):
    access_token = payload.token
    

    # Validate token with Google
    print("Google response:", access_token)
    response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        params={'access_token': access_token}
    )
    data = response.json()

    print("Google response data:", data)
    if 'error' in data:
        raise HTTPException(status_code=400, detail="Invalid or expired Google token")

    # Get or create user using Django ORM
    try:
        user = User.objects.get(email=data['email'])
    except User.DoesNotExist:
        user = User(
            email=data['email'],
            profile_pic=data.get('picture', ''),
            password=make_password(BaseUserManager().make_random_password())
        )
        user.save()

    # Generate JWT tokens using Django's SimpleJWT
    token = RefreshToken.for_user(user)
    return {
        "username": user.email,
        "access_token": str(token.access_token),
        "refresh_token": str(token),
        "user_id": user.id
    }



