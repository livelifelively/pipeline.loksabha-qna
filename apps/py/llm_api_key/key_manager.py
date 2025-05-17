"""
Key Manager module for managing multiple API keys in a round-robin fashion.
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Tuple

from dotenv import load_dotenv

from ..utils.project_root import find_project_root

# Add at module level (top of file)
_instance = None


class KeyManager:
    """
    Manages multiple API keys with round-robin selection and usage tracking.
    """

    @classmethod
    def get_instance(cls, service_name: str = "gemini"):
        """Get the singleton instance of KeyManager."""
        global _instance
        if _instance is None:
            _instance = cls(service_name)
        return _instance

    def __init__(self, service_name: str = "gemini", load_from_env: bool = True):
        """
        Initialize the Key Manager.

        Args:
            service_name: Name of the service (e.g., "gemini")
            load_from_env: Whether to load keys from environment variables
        """
        self.service_name = service_name
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.current_index = -1  # Start at -1 so first increment gives index 0
        self.reports_dir = Path(find_project_root()) / "reports" / "api_usage"

        # Create reports directory if it doesn't exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        if load_from_env:
            self._load_keys_from_env()

    def _load_keys_from_env(self) -> None:
        """Load API keys from environment variables."""
        load_dotenv()

        # Look for API keys in different formats
        base_key_name = f"{self.service_name.upper()}_API_KEY"

        # Check for single key format
        single_key = os.getenv(base_key_name)
        if single_key:
            self.add_key("default", single_key)

        # Also check for multiple keys with numeric suffixes
        i = 1
        while True:
            key_env_name = f"{base_key_name}_{i}"
            key_value = os.getenv(key_env_name)

            if not key_value:
                break

            self.add_key(f"{self.service_name}_{i}", key_value)
            i += 1

        # Concise but informative log
        print(f"[API Key Manager] Loaded {len(self.keys)} keys for {self.service_name}")

        if not self.keys:
            raise ValueError(f"No API keys found for service {self.service_name}")

    def add_key(self, key_name: str, key_value: str) -> None:
        """
        Add a new API key to the manager.

        Args:
            key_name: Reference name for the key
            key_value: The actual API key
        """
        self.keys[key_name] = {
            "value": key_value,
            "usage": {
                "daily_count": 0,
                "last_used": None,
                "minute_counts": [],
            },
            "enabled": True,
        }

    def get_next_key(self) -> Tuple[str, str]:
        """
        Get the next available API key in round-robin fashion.

        Returns:
            Tuple of (key_name, key_value)

        Raises:
            ValueError: If no enabled keys are available
        """
        if not self.keys:
            raise ValueError(f"No API keys available for {self.service_name}")

        # Convert to list for indexing
        key_items = list(self.keys.items())

        # Try each key in sequence, starting from the next one
        attempts = 0
        while attempts < len(key_items):
            # Move to next key position immediately
            self.current_index = (self.current_index + 1) % len(key_items)
            key_name, key_data = key_items[self.current_index]

            if key_data["enabled"]:
                # Update usage data
                now = datetime.now()
                key_data["usage"]["last_used"] = now
                key_data["usage"]["daily_count"] += 1

                # Track per-minute usage
                key_data["usage"]["minute_counts"].append(now)

                # Clean old minute counts (keep only last 10 minutes)
                key_data["usage"]["minute_counts"] = [
                    t for t in key_data["usage"]["minute_counts"] if (now - t).total_seconds() < 600
                ]

                return key_name, key_data["value"]

            attempts += 1

        raise ValueError("No enabled API keys available")

    def disable_key(self, key_name: str) -> None:
        """
        Disable a key (e.g., when quota is reached).

        Args:
            key_name: Name of the key to disable
        """
        if key_name in self.keys:
            self.keys[key_name]["enabled"] = False

    def enable_key(self, key_name: str) -> None:
        """
        Enable a previously disabled key.

        Args:
            key_name: Name of the key to enable
        """
        if key_name in self.keys:
            self.keys[key_name]["enabled"] = True

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for all keys.

        Returns:
            Dictionary with usage statistics
        """
        stats = {}
        for key_name, key_data in self.keys.items():
            stats[key_name] = {
                "daily_count": key_data["usage"]["daily_count"],
                "last_used": key_data["usage"]["last_used"].isoformat() if key_data["usage"]["last_used"] else None,
                "enabled": key_data["enabled"],
                "requests_last_minute": len(
                    [t for t in key_data["usage"]["minute_counts"] if (datetime.now() - t).total_seconds() < 60]
                ),
            }
        return stats

    def save_daily_report(self) -> None:
        """Save the current usage statistics to a daily report file."""
        today = date.today().isoformat()
        report_file = self.reports_dir / f"{self.service_name}_{today}.json"

        report_data = {"service": self.service_name, "date": today, "keys": {}}

        for key_name, key_data in self.keys.items():
            # Don't include the actual key value in the report
            report_data["keys"][key_name] = {
                "daily_count": key_data["usage"]["daily_count"],
                "last_used": key_data["usage"]["last_used"].isoformat() if key_data["usage"]["last_used"] else None,
                "enabled": key_data["enabled"],
            }

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

    def should_rate_limit(self, key_name: str, max_per_minute: int = 10) -> bool:
        """
        Check if a key should be rate limited.

        Args:
            key_name: Name of the key to check
            max_per_minute: Maximum requests allowed per minute

        Returns:
            True if the key should be rate limited
        """
        if key_name not in self.keys:
            return False

        # Count requests in the last minute
        now = datetime.now()
        minute_counts = self.keys[key_name]["usage"]["minute_counts"]
        recent_count = len([t for t in minute_counts if (now - t).total_seconds() < 60])

        return recent_count >= max_per_minute
