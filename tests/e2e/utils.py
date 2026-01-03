"""
Shared utilities for E2E tests.
"""

from typing import Optional, Dict, Any, List


class UserSession:
    """Helper class to manage user session data."""

    def __init__(self) -> None:
        self.email: Optional[str] = None
        self.user_id: Optional[str] = None
        self.access_token: Optional[str] = None
        self.projects: List[Dict[str, Any]] = []

    @property
    def headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if not self.access_token:
            raise ValueError("No access token available")
        return {"Authorization": f"Bearer {self.access_token}"}
