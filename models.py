from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    bio = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    posts = relationship("Posts", back_populates="owner")
    socials = relationship("Socials", back_populates="follow")


class Posts(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    post_body = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("Users", back_populates="posts")


class Socials(Base):
    __tablename__ = "socials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    follows_id = Column(Integer)

    follow = relationship("Users", back_populates="socials")
