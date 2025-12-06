# python imports
import os

# Third party imports
from rest_framework.throttling import SimpleRateThrottle

# Module imports
from plane.license.utils.instance_value import get_configuration_value


class ApiKeyRateThrottle(SimpleRateThrottle):
    scope = "api_key"

    def __init__(self):
        super().__init__()
        # Override the rate attribute dynamically from instance configuration
        (rate_limit,) = get_configuration_value(
            [{"key": "RATE_LIMIT_API_KEY", "default": os.environ.get("API_KEY_RATE_LIMIT", "60/minute")}]
        )
        self.rate = rate_limit or "60/minute"
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_cache_key(self, request, view):
        # Retrieve the API key from the request header
        api_key = request.headers.get("X-Api-Key")
        if not api_key:
            return None  # Allow the request if there's no API key

        # Use the API key as part of the cache key
        return f"{self.scope}:{api_key}"

    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)

        if allowed:
            now = self.timer()
            # Calculate the remaining limit and reset time
            history = self.cache.get(self.key, [])

            # Remove old histories
            while history and history[-1] <= now - self.duration:
                history.pop()

            # Calculate the requests
            num_requests = len(history)

            # Check available requests
            available = self.num_requests - num_requests

            # Unix timestamp for when the rate limit will reset
            reset_time = int(now + self.duration)

            # Add headers
            request.META["X-RateLimit-Remaining"] = max(0, available)
            request.META["X-RateLimit-Reset"] = reset_time

        return allowed


class ServiceTokenRateThrottle(SimpleRateThrottle):
    scope = "service_token"

    def __init__(self):
        super().__init__()
        # Override the rate attribute dynamically from instance configuration
        (rate_limit,) = get_configuration_value(
            [{"key": "RATE_LIMIT_SERVICE_TOKEN", "default": os.environ.get("RATE_LIMIT_SERVICE_TOKEN", "300/minute")}]
        )
        self.rate = rate_limit or "300/minute"
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_cache_key(self, request, view):
        # Retrieve the API key from the request header
        api_key = request.headers.get("X-Api-Key")
        if not api_key:
            return None  # Allow the request if there's no API key

        # Use the API key as part of the cache key
        return f"{self.scope}:{api_key}"

    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)

        if allowed:
            now = self.timer()
            # Calculate the remaining limit and reset time
            history = self.cache.get(self.key, [])

            # Remove old histories
            while history and history[-1] <= now - self.duration:
                history.pop()

            # Calculate the requests
            num_requests = len(history)

            # Check available requests
            available = self.num_requests - num_requests

            # Unix timestamp for when the rate limit will reset
            reset_time = int(now + self.duration)

            # Add headers
            request.META["X-RateLimit-Remaining"] = max(0, available)
            request.META["X-RateLimit-Reset"] = reset_time

        return allowed
