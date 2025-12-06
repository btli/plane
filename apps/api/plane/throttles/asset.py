# Python imports
import os

# Third party imports
from rest_framework.throttling import SimpleRateThrottle

# Module imports
from plane.license.utils.instance_value import get_configuration_value


class AssetRateThrottle(SimpleRateThrottle):
    scope = "asset_id"

    def __init__(self):
        super().__init__()
        # Override the rate attribute dynamically from instance configuration
        (rate_limit,) = get_configuration_value(
            [{"key": "RATE_LIMIT_ASSET", "default": os.environ.get("RATE_LIMIT_ASSET", "5/minute")}]
        )
        self.rate = rate_limit or "5/minute"
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_cache_key(self, request, view):
        asset_id = view.kwargs.get("asset_id")
        if not asset_id:
            return None
        return f"throttle_asset_{asset_id}"
