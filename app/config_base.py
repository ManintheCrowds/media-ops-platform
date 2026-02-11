"""Base configuration class with common validators for service configs."""

from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class BaseServiceConfig(BaseSettings):
    """Base configuration class for services with common validators."""
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_urls(cls, v, info):
        """Validate URL fields if they contain 'url' in the field name."""
        if info.field_name and 'url' in info.field_name.lower() and isinstance(v, str):
            try:
                result = urlparse(v)
                if not result.scheme or not result.netloc:
                    raise ValueError(f"Invalid URL format for {info.field_name}: {v}")
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                raise ValueError(f"Invalid URL format for {info.field_name}: {v}")
        return v
    
    @staticmethod
    def validate_path(path_str: str, must_exist: bool = False, must_be_creatable: bool = False) -> Path:
        """Validate a path string and return Path object.
        
        Args:
            path_str: Path string to validate
            must_exist: If True, path must exist
            must_be_creatable: If True, parent directory must be writable (for creation)
        
        Returns:
            Path object
            
        Raises:
            ValueError: If path validation fails
        """
        try:
            path = Path(path_str)
            
            if must_exist and not path.exists():
                raise ValueError(f"Path does not exist: {path_str}")
            
            if must_be_creatable:
                parent = path.parent
                if not parent.exists():
                    # Try to create parent directory
                    try:
                        parent.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        raise ValueError(f"Cannot create parent directory for {path_str}: {e}")
                elif not parent.is_dir():
                    raise ValueError(f"Parent path is not a directory: {parent}")
                # Check if parent is writable (approximate check)
                if not (parent.stat().st_mode & 0o200):
                    raise ValueError(f"Parent directory is not writable: {parent}")
            
            return path
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid path: {path_str} - {e}")
    
    @staticmethod
    def validate_positive_int(value: int, field_name: str = "field") -> int:
        """Validate that an integer is positive.
        
        Args:
            value: Integer value to validate
            field_name: Name of the field for error messages
            
        Returns:
            Validated integer
            
        Raises:
            ValueError: If value is not positive
        """
        if value <= 0:
            raise ValueError(f"{field_name} must be a positive integer, got {value}")
        return value
    
    @staticmethod
    def validate_non_empty_string(value: Optional[str], field_name: str = "field") -> Optional[str]:
        """Validate that a string is non-empty if provided.
        
        Args:
            value: String value to validate
            field_name: Name of the field for error messages
            
        Returns:
            Validated string or None
            
        Raises:
            ValueError: If value is an empty string
        """
        if value is not None and value.strip() == "":
            raise ValueError(f"{field_name} cannot be an empty string")
        return value

