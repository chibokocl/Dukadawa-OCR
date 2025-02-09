# app/models.py
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from .database import Base
from uuid import UUID, uuid4

# SQLAlchemy Models
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    certificate_number = Column(String(50), unique=True, index=True)
    classification = Column(String(100))
    brand_name = Column(String(200))
    generic_name = Column(String(200))
    dosage_form = Column(String(100))
    manufacturer_country = Column(String(100))
    strength = Column(String(100))
    manufacturer = Column(String(200))
    self_administered = Column(Boolean, default=False)
    description = Column(Text)
    precaution = Column(Text)
    display_name = Column(String(300))
    pack_size = Column(String(50))
    image_url = Column(String(500))
    expiry_date = Column(String)
    batch_number = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(Integer, index=True)

# Pydantic Models for Authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# Pydantic Models for Product
class ProductBase(BaseModel):
    certificate_number: Optional[str] = None
    classification: Optional[str] = None
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage_form: Optional[str] = None
    manufacturer_country: Optional[str] = None
    strength: Optional[str] = None
    manufacturer: Optional[str] = None
    self_administered: Optional[bool] = None
    description: Optional[str] = None
    precaution: Optional[str] = None
    display_name: Optional[str] = None
    pack_size: Optional[str] = None
    image_url: Optional[str] = None
    expiry_date: Optional[date] = None
    batch_number: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductData(BaseModel):
    id: int | None = None
    created_at: datetime | None = None
    certificate_number: str | None = None
    brand_name: str | None = None
    generic_name: str | None = None
    dosage_form: str | None = None
    manufacturer: str | None = None
    strength: str | None = None
    batch_number: str | None = None
    expiry_date: str | None = None
    image_url: str | None = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True