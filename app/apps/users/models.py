from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from app.apps.startups.models import Startup
    from app.apps.auth.models import OAuthAccount


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    twitter_handle: Optional[str] = None
    website_url: Optional[str] = None
    country: str = Field(default="Tanzania")
    primary_provider: str
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    startups: list["Startup"] = Relationship(back_populates="founder")
    oauth_accounts: list["OAuthAccount"] = Relationship(back_populates="user")
