# General Topic Categorization (Non-Tech)

GENERAL_CATEGORY_MAP = {
    # Biography / People
    "born": "Personal Info",
    "died": "Personal Info",
    "birth": "Personal Info",
    "death": "Personal Info",
    "education": "Background",
    "alma mater": "Background",
    "spouse": "Personal Info",
    "children": "Personal Info",
    "career": "Professional",
    "known for": "Professional",
    "office": "Professional",
    "political party": "Professional",
    "awards": "Achievements",
    "books": "Works",
    "writings": "Works",
    
    # Legal / Documents
    "enacted by": "Legal Info",
    "date enacted": "Dates",
    "date effective": "Dates",
    "citation": "Legal Info",
    "territorial extent": "Scope",
    "status": "Legal Info",
    
    # General
    "type": "General Info",
    "industry": "Business",
    "founded": "History",
    "headquarters": "Location",
    "owner": "Ownership"
}

def get_general_aspect_group(aspect: str) -> str:
    """Return the high-level category for a general aspect."""
    aspect_lower = aspect.lower()
    
    # Check for direct mapping
    if aspect_lower in GENERAL_CATEGORY_MAP:
        return GENERAL_CATEGORY_MAP[aspect_lower]
        
    # Check for keywords within aspect
    if any(k in aspect_lower for k in ["life", "birth", "born"]): return "Personal Info"
    if any(k in aspect_lower for k in ["work", "career", "job"]): return "Professional"
    if any(k in aspect_lower for k in ["book", "paper", "author"]): return "Works"
    if any(k in aspect_lower for k in ["law", "act", "legal", "section"]): return "Legal Info"
    
    return "Details"
