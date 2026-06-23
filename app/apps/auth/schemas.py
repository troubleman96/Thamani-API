from pydantic import BaseModel
from typing import Optional


class OAuthCallbackParams(BaseModel):
    code: str
    state: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthUserOut(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str]
    provider: str
    is_verified: bool
