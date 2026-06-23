from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid


class SavedStartup(SQLModel, table=True):
    __tablename__ = "saved_startups"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    startup_id: str = Field(foreign_key="startups.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
