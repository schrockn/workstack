import hashlib


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_combined_hash(*contents: str) -> str:
    """Compute hash of multiple contents combined."""
    combined = "".join(contents)
    return compute_hash(combined)
