from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func
from datetime import datetime
from pydantic import BaseModel

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    certificate_number = Column(String(50))
    brand_name = Column(String(200))
    generic_name = Column(String(200))
    dosage_form = Column(String(100))
    manufacturer = Column(String(200))
    strength = Column(String(100))
    batch_number = Column(String(50))
    expiry_date = Column(String)
    image_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, default=0)
    classification = Column(String(100))
    manufacturer_country = Column(String(100))
    self_administered = Column(Boolean)
    description = Column(Text)
    precaution = Column(Text)
    display_name = Column(String(300))
    pack_size = Column(String(50))
    updated_at = Column(DateTime)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables() 