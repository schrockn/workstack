from mdstack.hashing import compute_combined_hash, compute_hash


def test_compute_hash_deterministic():
    """Hash should be deterministic."""
    content = "test content"
    hash1 = compute_hash(content)
    hash2 = compute_hash(content)

    assert hash1 == hash2


def test_compute_hash_different_for_different_content():
    """Different content should produce different hashes."""
    hash1 = compute_hash("content1")
    hash2 = compute_hash("content2")

    assert hash1 != hash2


def test_compute_combined_hash():
    """Should hash multiple strings combined."""
    combined = compute_combined_hash("foo", "bar", "baz")
    direct = compute_hash("foobarbaz")

    assert combined == direct
