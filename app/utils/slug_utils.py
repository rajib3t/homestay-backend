import re
import unicodedata
from typing import Optional


def generate_slug(name: str, existing_slugs: Optional[list] = None) -> str:
    """
    Generate a URL-friendly slug from a name.
    
    Args:
        name: The name to convert to slug
        existing_slugs: List of existing slugs to avoid duplicates
        
    Returns:
        A URL-friendly slug
    """
    if not name:
        raise ValueError("Name cannot be empty for slug generation")
    
    # Normalize Unicode characters (e.g., convert á to a)
    normalized_name = unicodedata.normalize('NFKD', name)
    
    # Remove diacritics (accents)
    ascii_name = ''.join(c for c in normalized_name if unicodedata.category(c) != 'Mn')
    
    # Convert to lowercase and replace non-alphanumeric characters with hyphens
    base_slug = re.sub(r'[^a-z0-9]+', '-', ascii_name.lower().strip())
    
    # Remove leading/trailing hyphens and replace multiple hyphens with single
    base_slug = re.sub(r'-+', '-', base_slug.strip('-'))
    
    if not base_slug:
        raise ValueError("Invalid name for slug generation")
    
    # If no existing slugs provided, return base slug
    if not existing_slugs:
        return base_slug
    
    # Check for duplicates and add suffix if needed
    slug = base_slug
    counter = 1
    
    while slug in existing_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


def validate_slug(slug: str) -> bool:
    """
    Validate if a slug is in correct format.
    
    Args:
        slug: The slug to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not slug:
        return False
    
    # Slug should only contain lowercase letters, numbers, and hyphens
    # Should not start or end with hyphen, and no consecutive hyphens
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    return bool(re.match(pattern, slug))
