from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.AI.database.postgres import PostgresDatabase
from backend.AI.services.auth_service import authenticate, create_access_token, create_user, get_user_for_token, revoke_token


router = APIRouter()
bearer = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


def current_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> tuple[str, dict]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = get_user_for_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
    return credentials.credentials, user


@router.post("/register", status_code=201)
def register(req: RegisterRequest):
    PostgresDatabase.initialize()
    try:
        user = create_user(req.email, req.password, req.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    token, expires_at = create_access_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at, "user": user}


@router.post("/login")
def login(req: LoginRequest):
    PostgresDatabase.initialize()
    try:
        user = authenticate(req.email, req.password)
    except ValueError:
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token, expires_at = create_access_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at, "user": user}


@router.get("/me")
def me(auth=Depends(current_auth)):
    return {"user": auth[1]}


@router.post("/logout")
def logout(auth=Depends(current_auth)):
    revoke_token(auth[0])
    return {"status": "success"}
