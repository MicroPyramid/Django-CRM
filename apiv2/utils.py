# fastapi_app/main.py
import os
import django
# fastapi_app/routers/products.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, TokenBackendError
from crm.settings import SECRET_KEY  # Use Django settings for shared configuration

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/google")

# Use Django's secret key and the SIMPLE_JWT algorithm configuration (defaulting to HS256)
ALGORITHM = 'HS256'

def verify_token(token: str = Depends(oauth2_scheme)):
    token_backend = TokenBackend(algorithm=ALGORITHM, signing_key=SECRET_KEY)
    try:
        # Decode the token and verify its signature and claims.
        validated_token = token_backend.decode(token, verify=True)
        return validated_token
    except (TokenError, InvalidToken, TokenBackendError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )