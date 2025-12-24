"""Text processing utilities for job descriptions."""

import re
from typing import List, Set, Dict, Optional


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for matching.
    
    Args:
        skill: Skill name to normalize
    
    Returns:
        Normalized skill name (lowercase, no special chars)
    """
    # Convert to lowercase
    skill = skill.lower()
    
    # Remove special characters except spaces and hyphens
    skill = re.sub(r'[^\w\s-]', '', skill)
    
    # Replace spaces and hyphens with underscores
    skill = re.sub(r'[\s-]+', '_', skill)
    
    return skill.strip('_')


def get_skill_variants(skill: str) -> Set[str]:
    """Get variations of a skill name.
    
    Args:
        skill: Base skill name
    
    Returns:
        Set of skill variants
    """
    variants = set()
    normalized = normalize_skill_name(skill)
    
    # Add normalized version
    variants.add(normalized)
    
    # Add original lowercase
    variants.add(skill.lower())
    
    # Add with underscores
    variants.add(skill.replace(' ', '_').lower())
    variants.add(skill.replace('-', '_').lower())
    
    # Add with hyphens
    variants.add(skill.replace(' ', '-').lower())
    variants.add(skill.replace('_', '-').lower())
    
    # Special cases
    if skill.lower() in ['ai', 'artificial intelligence']:
        variants.update(['ai', 'artificial_intelligence', 'machine_learning', 'ml'])
    elif skill.lower() in ['ml', 'machine learning']:
        variants.update(['ml', 'machine_learning', 'ai', 'artificial_intelligence'])
    elif skill.lower() in ['python', 'python3']:
        variants.update(['python', 'python3', 'py'])
    elif skill.lower() in ['javascript', 'js']:
        variants.update(['javascript', 'js', 'node', 'nodejs'])
    
    return variants


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
    
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Extract words (alphanumeric + common tech terms)
    words = re.findall(r'\b[a-z][a-z0-9-]+\b', text)
    
    # Filter by length and common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now'
    }
    
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stop_words
    ]
    
    return keywords


def extract_requirements(text: str) -> Dict[str, List[str]]:
    """Extract requirements from job description.
    
    Args:
        text: Job description text
    
    Returns:
        Dictionary with 'required' and 'preferred' lists
    """
    requirements = {
        'required': [],
        'preferred': []
    }
    
    if not text:
        return requirements
    
    # Look for "Requirements:" or "Required:" sections
    req_pattern = re.compile(
        r'(?:requirements?|required|must have|qualifications?):\s*(.+?)(?:\n\n|\n[A-Z]|$)',
        re.IGNORECASE | re.DOTALL
    )
    
    # Look for "Preferred:" or "Nice to have" sections
    pref_pattern = re.compile(
        r'(?:preferred|nice to have|bonus|plus):\s*(.+?)(?:\n\n|\n[A-Z]|$)',
        re.IGNORECASE | re.DOTALL
    )
    
    req_match = req_pattern.search(text)
    if req_match:
        req_text = req_match.group(1)
        # Split by bullets or newlines
        req_items = re.split(r'[•\-\*]\s*|\n', req_text)
        requirements['required'] = [
            item.strip() for item in req_items
            if item.strip() and len(item.strip()) > 10
        ]
    
    pref_match = pref_pattern.search(text)
    if pref_match:
        pref_text = pref_match.group(1)
        pref_items = re.split(r'[•\-\*]\s*|\n', pref_text)
        requirements['preferred'] = [
            item.strip() for item in pref_items
            if item.strip() and len(item.strip()) > 10
        ]
    
    return requirements


def extract_experience_level(text: str) -> Optional[str]:
    """Extract experience level from job description.
    
    Args:
        text: Job description text
    
    Returns:
        Experience level (entry, mid, senior, etc.) or None
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Look for experience level keywords
    if re.search(r'\b(entry|junior|associate|level 1|0-2 years?)\b', text_lower):
        return 'entry'
    elif re.search(r'\b(mid|middle|intermediate|2-5 years?|3-5 years?)\b', text_lower):
        return 'mid'
    elif re.search(r'\b(senior|lead|principal|5\+ years?|5-10 years?)\b', text_lower):
        return 'senior'
    elif re.search(r'\b(executive|director|vp|10\+ years?)\b', text_lower):
        return 'executive'
    
    return None

