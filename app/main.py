# app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import numpy as np
import cv2
from typing import List
import redis
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from .models import ProductData, Product, ProductCreate, Token, TokenData, User, UserCreate, UserInDB, UserDB
from .ocr.processor import OCRProcessor
from .config import settings
from .logger import get_logger
from .database import get_db, engine, Base

# Initialize logger
logger = get_logger()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize Redis for caching (optional)
REDIS_AVAILABLE = False
redis_client = None

try:
    redis_client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
    # Test the connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connection established successfully")
except (redis.ConnectionError, redis.TimeoutError):
    logger.warning("Redis connection failed. Running without caching and rate limiting")
except Exception as e:
    logger.warning(f"Unexpected error with Redis: {str(e)}. Running without caching and rate limiting")

app = FastAPI(
    title=settings.APP_NAME,
    description="API for processing pharmaceutical product images using OCR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

ocr_processor = OCRProcessor()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except jwt.JWTError:
        return None
    user = get_user(db, username=token_data.username)
    if user is None:
        return None
    return user

def get_user(db: Session, username: str):
    return db.query(UserDB).filter(UserDB.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=User)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    db_user = UserDB(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if not REDIS_AVAILABLE or request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
        
    client_ip = request.client.host
    request_count = redis_client.get(f"rate_limit:{client_ip}")
    
    if request_count and int(request_count) > settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(429, "Too many requests")
    
    redis_client.incr(f"rate_limit:{client_ip}")
    redis_client.expire(f"rate_limit:{client_ip}", 60)
    
    response = await call_next(request)
    return response

@app.post(f"{settings.API_V1_STR}/process-image/", response_model=ProductData)
async def process_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Processing single image: {file.filename}")
    
    if file.content_type not in settings.SUPPORTED_FORMATS:
        logger.error(f"Unsupported file format: {file.content_type}")
        raise HTTPException(400, f"Unsupported file format. Supported formats: {settings.SUPPORTED_FORMATS}")
    
    try:
        file_size = 0
        contents = bytearray()
        
        # Read file in chunks to check size
        chunk_size = 1024 * 1024  # 1MB chunks
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE:
                logger.error(f"File too large: {file_size} bytes")
                raise HTTPException(400, f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE} bytes")
            contents.extend(chunk)
        
        await file.seek(0)
        
        # Check cache if Redis is available
        if REDIS_AVAILABLE:
            cache_key = f"image:{hash(contents)}"
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return ProductData.parse_raw(cached_result)
        
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            logger.error(f"Invalid image format or corrupted file: {file.filename}")
            raise HTTPException(400, "Invalid image format or corrupted file")
        
        product_data = ocr_processor.extract_product_info(image)
        
        # Save to database
        db_product = Product(**product_data.dict(), user_id=current_user.id)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        # Cache the result if Redis is available
        if REDIS_AVAILABLE:
            redis_client.setex(
                cache_key,
                settings.CACHE_TTL,
                ProductData.from_orm(db_product).json()
            )
        
        logger.info(f"Successfully processed image: {file.filename}")
        return ProductData.from_orm(db_product)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing image {file.filename}: {str(e)}")
        raise HTTPException(500, f"Error processing image: {str(e)}")

@app.post(f"{settings.API_V1_STR}/process-bulk/", response_model=List[ProductData])
async def process_bulk_images(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Processing bulk images: {len(files)} files")
    results = []
    errors = []
    
    for file in files:
        try:
            if file.content_type not in settings.SUPPORTED_FORMATS:
                logger.warning(f"Skipping unsupported file format: {file.filename}")
                errors.append(f"Skipped {file.filename}: Unsupported format")
                continue
            
            contents = await file.read()
            if len(contents) > settings.MAX_UPLOAD_SIZE:
                logger.warning(f"Skipping file too large: {file.filename}")
                errors.append(f"Skipped {file.filename}: File too large")
                continue
            
            # Check cache if Redis is available
            if REDIS_AVAILABLE:
                cache_key = f"image:{hash(contents)}"
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    results.append(ProductData.parse_raw(cached_result))
                    continue
                
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is not None:
                product_data = ocr_processor.extract_product_info(image)
                
                # Save to database
                db_product = Product(**product_data.dict(), user_id=current_user.id)
                db.add(db_product)
                db.commit()
                db.refresh(db_product)
                
                # Cache the result if Redis is available
                if REDIS_AVAILABLE:
                    redis_client.setex(
                        cache_key,
                        settings.CACHE_TTL,
                        ProductData.from_orm(db_product).json()
                    )
                
                results.append(ProductData.from_orm(db_product))
                logger.info(f"Successfully processed: {file.filename}")
            else:
                logger.error(f"Invalid image format: {file.filename}")
                errors.append(f"Failed to process {file.filename}: Invalid image format")
                
        except Exception as e:
            logger.exception(f"Error processing {file.filename}: {str(e)}")
            errors.append(f"Failed to process {file.filename}: {str(e)}")
            continue
    
    if not results:
        logger.error("No images were successfully processed")
        raise HTTPException(400, f"No images were successfully processed. Errors: {'; '.join(errors)}")
    
    if errors:
        logger.warning(f"Processed with errors: {'; '.join(errors)}")
    
    return results

@app.get("/")
async def root():
    return {
        "message": "Welcome to Pharmacy OCR API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Pharmacy OCR API")
    # Add any startup initialization here

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Pharmacy OCR API")
    # Add any cleanup code here