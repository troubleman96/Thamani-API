from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class VerificationCredential(SQLModel, table=True):
    """
    Stores AES-256 encrypted provider credentials per startup.
    encrypted_secret must never be logged or exposed in any response.
    """
    __tablename__ = "verification_credentials"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    startup_id: str = Field(foreign_key="startups.id", index=True, unique=True)
    provider: str
    account_identifier: str
    encrypted_secret: str
    is_active: bool = Field(default=True)
    last_verified_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
