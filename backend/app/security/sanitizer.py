import html
import re

def escape_html(text: str) -> str:
    """
    Encode dangerous HTML characters: &, <, >, ", '
    Used to mitigate Cross-Site Scripting (LAB-003, LAB-004).
    """
    if not text:
        return ""
    return html.escape(str(text), quote=True)

def sanitize_comment(raw_text: str, secure_mode: bool = False) -> str:
    """
    Sanitize user comments.
    In vulnerable mode: returns unescaped raw string.
    In secure mode: escapes HTML entities.
    """
    if not secure_mode:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-003 Stored XSS)
        return raw_text
    return escape_html(raw_text)

def sanitize_search_query(query: str, secure_mode: bool = False) -> str:
    """
    Sanitize search query strings reflected in response bodies.
    In vulnerable mode: returns query as-is.
    In secure mode: escapes HTML entities and strips control chars.
    """
    if not secure_mode:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-004 Reflected XSS)
        return query
    clean = re.sub(r'[\x00-\x1f\x7f]', '', query)
    return escape_html(clean)
