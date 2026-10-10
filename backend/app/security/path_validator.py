import os
from fastapi import HTTPException, status

def resolve_safe_filepath(base_directory: str, requested_filename: str, secure_mode: bool = False) -> str:
    """
    Validate and resolve file path to prevent Directory / Path Traversal (LAB-007).
    
    Vulnerable mode:
      Blindly joins requested filename, allowing '../' sequences to escape base_directory.
      
    Secure mode:
      Canonicalizes the target path and verifies it resides within base_directory.
    """
    if not secure_mode:
        # INTENTIONALLY VULNERABLE FOR SECURITY TRAINING (LAB-007 Path Traversal)
        # Does not canonicalize or check directory bounds
        target_path = os.path.join(base_directory, requested_filename)
        return target_path
    
    # Secure implementation:
    # 1. Strip leading slashes and null bytes
    sanitized_filename = os.path.basename(requested_filename.replace("\x00", ""))
    
    # 2. Canonicalize real path
    canonical_base = os.path.realpath(base_directory)
    target_path = os.path.realpath(os.path.join(canonical_base, sanitized_filename))
    
    # 3. Path boundary verification (common prefix check)
    if not target_path.startswith(canonical_base):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Path traversal attempt detected."
        )
        
    return target_path
