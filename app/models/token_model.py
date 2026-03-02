from datetime import datetime
from bson import ObjectId


class TokenType:
    """Token type constants."""
    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    
    VALID_TYPES = [ACCESS, REFRESH, RESET_PASSWORD, EMAIL_VERIFICATION]


class Token:
    """Token model for MongoDB."""
    
    COLLECTION_NAME = "tokens"
    
    def __init__(self, user_id, token, token_type=TokenType.REFRESH, 
                 is_revoked=False, expires_at=None, _id=None, created_at=None, additional_claims=None):
        """
        Initialize a Token object.
        
        Args:
            user_id (str or ObjectId): ID of the user this token belongs to
            token (str): The token string
            token_type (str): Type of token (default: refresh)
            is_revoked (bool): Whether the token has been revoked
            expires_at (datetime): When the token expires
            _id (ObjectId, optional): MongoDB document ID
            created_at (datetime, optional): Creation timestamp
            additional_claims (dict, optional): Additional claims for the token
        """
        self._id = _id
        self.user_id = user_id if isinstance(user_id, ObjectId) else ObjectId(user_id)
        self.token = token
        self.token_type = token_type
        self.is_revoked = is_revoked
        self.expires_at = expires_at
        self.created_at = created_at or datetime.utcnow()
        self.additional_claims = additional_claims or {}

    def to_dict(self):
        """Convert token object to dictionary."""
        return {
            "id": str(self._id) if self._id else None,
            "user_id": str(self.user_id),
            "token": self.token,
            "token_type": self.token_type,
            "is_revoked": self.is_revoked,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "additional_claims": self.additional_claims
        }
    
    def to_mongo_dict(self):
        """Convert token object to MongoDB document format."""
        doc = {
            "user_id": self.user_id,
            "token": self.token,
            "token_type": self.token_type,
            "is_revoked": self.is_revoked,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "additional_claims": self.additional_claims
        }
        
        if self._id:
            doc["_id"] = self._id if isinstance(self._id, ObjectId) else ObjectId(self._id)
            
        return doc
    
    @staticmethod
    def from_mongo_doc(doc):
        """Create Token object from MongoDB document."""
        if not doc:
            return None
            
        return Token(
            user_id=doc.get("user_id"),
            token=doc.get("token"),
            token_type=doc.get("token_type"),
            is_revoked=doc.get("is_revoked", False),
            expires_at=doc.get("expires_at"),
            _id=doc.get("_id"),
            created_at=doc.get("created_at"),
            additional_claims=doc.get("additional_claims", {})
        )
