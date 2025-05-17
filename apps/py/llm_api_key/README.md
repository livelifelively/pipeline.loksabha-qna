# LLM API Key Management

This module provides a solution for managing multiple API keys for LLM services (like Gemini), implementing round-robin rotation to maximize free tier usage and avoid rate limits.

## Rationale

Large Language Model APIs often provide:

- Free tiers with daily quotas
- Rate limits (requests per minute)
- Usage-based billing

This module helps you:

1. **Maximize Free Usage**: Rotate through multiple API keys to stay within free tier limits
2. **Avoid Rate Limiting**: Track and limit request frequency
3. **Monitor Usage**: Generate usage reports for cost management

## Components

- `KeyManager`: Core component for key rotation and tracking
- `UsageTracker`: Detailed usage tracking and reporting
- `RateLimiter`: Prevents hitting rate limits (RPM/daily limits)

## Quick Start

```python
from apps.py.llm_api_key import KeyManager

# Initialize with keys from environment variables
key_manager = KeyManager(service_name="gemini")

# Get the next available key in round-robin fashion
key_name, api_key = key_manager.get_next_key()

# Use the key with your API client
response = call_api_with_key(api_key)

# Optional: Save usage report
key_manager.save_daily_report()
```

## Environment Variables

Set up your API keys in your .env file:

### Single key

```
GEMINI_API_KEY=your_api_key
```

### Multiple keys

```
GEMINI_API_KEY_1 = first_api_key
GEMINI_API_KEY_2=second_api_key
GEMINI_API_KEY_3=third_api_key
```

## Advanced Usage

### Rate Limiting

```python
from apps.py.llm_api_key.rate_limiter import RateLimiter

# Create a rate limiter (10 RPM, 1000 per day)
limiter = RateLimiter(requests_per_minute=10, requests_per_day=1000)

# Option 1: Use as a decorator
@limiter.limit_sync
def my_api_function():
    # This function will be rate-limited
    return call_api()

# Option 2: Manual control
def another_function():
    limiter.wait_if_needed()  # Will wait if necessary
    return call_api()
```

### Usage Tracking

```python
from apps.py.llm_api_key.usage_tracker import UsageTracker

# Create a tracker
tracker = UsageTracker(service_name="gemini")

# Record API usage
tracker.record_usage(
    key_name="default",
    success=True,
    cost=1.0  # Optional: track tokens or other cost metrics
)

# Get usage report
report = tracker.get_usage_report()
print(f"Total API calls today: {sum(k['total_calls'] for k in report.values())}")

# Get historical usage (last 7 days)
historical = tracker.get_historical_report(days=7)
```

## Integration with Gemini API

To integrate with the existing Gemini API code, you can modify the `init_gemini` function:

```python
from apps.py.llm_api_key import KeyManager

def init_gemini() -> Any:
    """Initialize Gemini API with API key from key manager."""
    key_manager = KeyManager(service_name="gemini")
    key_name, api_key = key_manager.get_next_key()

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")
```

## Reports

Usage reports are saved in `reports/api_usage/` with filenames like `gemini_2023-05-25.json`.
