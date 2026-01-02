from datetime import datetime, timedelta, timezone

from api.v1.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password
        # Should be able to verify
        assert verify_password(password, hashed) is True
        # Wrong password should fail
        assert verify_password("wrongpassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"

        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)

        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "samepassword"

        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Should be different due to random salt
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test verification of valid token."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"

        payload = verify_token(invalid_token)

        assert payload is None

    def test_verify_expired_token(self):
        """Test verification of expired token."""
        data = {"sub": "user123"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        payload = verify_token(token)

        assert payload is None

    def test_token_custom_expiry(self):
        """Test token with custom expiry."""
        data = {"sub": "user123"}
        custom_expiry = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=custom_expiry)

        payload = verify_token(token)

        assert payload is not None
        # Check expiry is roughly correct (within 1 minute tolerance)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + custom_expiry
        assert abs((exp_time - expected_exp).total_seconds()) < 60
