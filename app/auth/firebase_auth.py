from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import firebase_admin
from firebase_admin import auth, credentials

from app.config import get_settings

security = HTTPBearer(auto_error=False)

settings = get_settings()

if not firebase_admin._apps:
    cred = credentials.Certificate(
        settings.firebase_credentials_path
    )

    firebase_admin.initialize_app(cred)


async def get_current_user(
    credentials_header: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials_header:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization token",
        )

    token = credentials_header.credentials

    # GUEST MODE BYPASS: Check for mock guest token
    if token == "guest_mock_token_identity":
        return {
            "uid": "guest_123",
            "email": "guest@aistory.com",
            "name": "Guest Player",
        }

    try:
        decoded_token = auth.verify_id_token(token)

        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
        }

    except Exception as exc:
        print("Firebase verify error:", repr(exc))

        raise HTTPException(
            status_code=401,
            detail=f"Invalid Firebase token: {str(exc)}",
        )