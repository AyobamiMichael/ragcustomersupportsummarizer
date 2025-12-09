"""
 Input validation utilities 
"""

import re
from typing import Optional

def validate_text_length(text: str, min_length: int = 10, 
                        max_length: int = 10000) ->  tuple[bool, Optional[str]]:
     """
    Validate text length
    
    Returns:
        (is_valid, error_message)
    """
     if not text or not text.strip():
         return False, "Text cannot be empty"
     
     length = len(text)
     if length < min_length:
            return False, f"Text too short (minimum {min_length} characters)"
    
     if length > max_length:
            return False, f"Text too long (maximum {max_length} characters)"
    
     return True, None

def sanitize_input(text: str) -> str:

    """Sanitize user input"""
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit consecutive newlines
    text = re.sub(r'\n{5,}', '\n\n\n', text)
    
    # Remove any control characters except newlines and tabs
    text = ''.join(char for char in text if char >= ' ' or char in '\n\t')
    
    return text.strip()

def is_valid_mode(mode: str) -> bool:
     """Check if pipeline is valid"""
     valid_modes = {'extractive', 'semantic', 'abstractive'}
     return mode.lower() in valid_modes

def validate_top_k(top_k:int, max_k: int=10) -> tuple[bool, Optional[str]]:
     """Validate top_k parameter"""
     if top_k < 1:
          return False, "top_k must be at least 1"
     if top_k > max_k:
          return False,  f"top_k cannot exceed {max_k}"
    
     return True, None