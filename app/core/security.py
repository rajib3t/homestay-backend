from datetime import datetime, timedelta, timezone
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError
import bcrypt
from app.core.config import settings
from app.core.exceptions import TokenExpiredError, TokenInvalidError

class JWTHandler:

    @staticmethod
    def create_access_token(data: dict, additional_claims: dict = None):
        to_encode = data.copy()
        if additional_claims:
            to_encode.update(additional_claims)
        
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict, additional_claims: dict = None, expires_at=None):
        to_encode = data.copy()
        if additional_claims:
            to_encode.update(additional_claims)
        if expires_at is None:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        else:
            expire = expires_at

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt, expire

    @staticmethod
    def decode_token(token: str):
        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except ExpiredSignatureError as e:
            raise TokenExpiredError(str(e))
        except (JWTClaimsError, JWTError) as e:
            raise TokenInvalidError(str(e))

class PasswordHasher:

    @staticmethod
    def hash_password(password: str) -> str:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)