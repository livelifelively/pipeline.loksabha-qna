"""
Track API usage and generate reports.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.project_root import find_project_root


class UsageTracker:
    """Track API usage and generate reports."""

    def __init__(self, service_name: str):
        """
        Initialize the usage tracker.

        Args:
            service_name: Name of the service being tracked
        """
        self.service_name = service_name
        self.reports_dir = Path(find_project_root()) / "reports" / "api_usage"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.current_date = date.today().isoformat()

        # Initialize today's usage
        self.today_usage: Dict[str, Dict[str, Any]] = {}

        # Try to load existing usage data for today
        self._load_current_usage()

    def _load_current_usage(self) -> None:
        """Load usage data for today if it exists."""
        report_file = self.reports_dir / f"{self.service_name}_{self.current_date}.json"

        if report_file.exists():
            try:
                with open(report_file, "r") as f:
                    data = json.load(f)
                    if "keys" in data:
                        self.today_usage = data["keys"]
            except (json.JSONDecodeError, IOError):
                # If file exists but is invalid, start fresh
                self.today_usage = {}

    def record_usage(self, key_name: str, success: bool = True, cost: Optional[float] = None) -> None:
        """
        Record API usage for a specific key.

        Args:
            key_name: Name of the key used
            success: Whether the API call was successful
            cost: Optional cost information (e.g., token count)
        """
        if key_name not in self.today_usage:
            self.today_usage[key_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_cost": 0.0,
                "timestamps": [],
            }

        # Update counts
        self.today_usage[key_name]["total_calls"] += 1
        if success:
            self.today_usage[key_name]["successful_calls"] += 1
        else:
            self.today_usage[key_name]["failed_calls"] += 1

        # Update cost if provided
        if cost is not None:
            self.today_usage[key_name]["total_cost"] += cost

        # Record timestamp
        self.today_usage[key_name]["timestamps"].append(datetime.now().isoformat())

        # Save updated data
        self._save_current_usage()

    def _save_current_usage(self) -> None:
        """Save current usage data to the report file."""
        report_file = self.reports_dir / f"{self.service_name}_{self.current_date}.json"

        report_data = {"service": self.service_name, "date": self.current_date, "keys": self.today_usage}

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

    def get_usage_report(self, key_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage report for today.

        Args:
            key_name: Optional key name to filter report

        Returns:
            Dictionary with usage statistics
        """
        if key_name:
            return self.today_usage.get(key_name, {})
        return self.today_usage

    def get_historical_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Get historical usage report for the specified number of days.

        Args:
            days: Number of days to include in report

        Returns:
            Dictionary with usage statistics by day
        """
        historical_data = {}

        # Find all report files and sort by date
        report_files = list(self.reports_dir.glob(f"{self.service_name}_*.json"))
        report_files.sort(reverse=True)

        # Load data from the most recent 'days' files
        for file in report_files[:days]:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    if "date" in data:
                        historical_data[data["date"]] = data.get("keys", {})
            except (json.JSONDecodeError, IOError):
                continue

        return historical_data
