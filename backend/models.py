from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    password = Column(
        String,
        nullable=True
    )

    is_verified = Column(
        Boolean,
        default=False
    )

    verification_token = Column(
        String,
        nullable=True
    )

    reset_token = Column(
        String,
        nullable=True
    )

    google_id = Column(
        String,
        nullable=True
    )

    auth_provider = Column(
        String,
        default="email"
    )