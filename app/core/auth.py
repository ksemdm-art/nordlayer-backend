from datetime import datetime, timedelta
from typing import Optional, Union
import hashlib
import secrets
from jose import JWTError, jwt
from app.core.config import settings

def create_access_token(
    subject: Union[str, int], 
    expires_delta: Optional[timedelta] = None,
    is_admin: bool = False
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "is_admin": is_admin,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    # Extract salt and hash from stored password
    try:
        salt, stored_hash = hashed_password.split('$', 1)
        computed_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return computed_hash == stored_hash
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    """Get password hash with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${password_hash}"