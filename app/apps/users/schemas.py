from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserPublicOut(BaseModel):
    id: str
    full_name: str
    avatar_url: Optional[str]
    bio: Optional[str]
    country: str
    twitter_handle: Optional[str]
    website_url: Optional[str]
    startup_count: int
    created_at: datetime


class UserPrivateOut(UserPublicOut):
    email: str
    is_verified: bool
    primary_provider: str


class UserUpdateIn(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    twitter_handle: Optional[str] = None
    website_url: Optional[str] = None
    country: Optional[str] = None
