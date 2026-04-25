from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from starlette import status

from server.deps import get_user_repository
from server.services.auth_service import AuthService
from server.services.jwt_service import get_jwt_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/authorize")
async def oauth_authorization_stub():
    """Declared in /.well-known/oauth-authorization-server; interactive code flow is not implemented."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use POST /auth/token (password grant) or a pre-issued Bearer JWT for MCP.",
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    repo = get_user_repository()
    auth = AuthService(jwt_service=get_jwt_service())
    user = await auth.authenticate_async(repo, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    token = auth.issue_access_token(user)
    return TokenResponse(access_token=token, token_type="bearer")
