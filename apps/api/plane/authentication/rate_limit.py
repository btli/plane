# Python imports
import os

# Third party imports
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.authentication.adapter.error import (
    AuthenticationException,
    AUTHENTICATION_ERROR_CODES,
)
from plane.license.utils.instance_value import get_configuration_value


class AuthenticationThrottle(AnonRateThrottle):
    scope = "authentication"

    def __init__(self):
        # Get rate from instance configuration BEFORE calling super().__init__()
        (rate_limit,) = get_configuration_value(
            [{"key": "RATE_LIMIT_AUTHENTICATION", "default": os.environ.get("RATE_LIMIT_AUTHENTICATION", "30/minute")}]
        )
        self.rate = rate_limit or "30/minute"
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def throttle_failure_view(self, request, *args, **kwargs):
        try:
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["RATE_LIMIT_EXCEEDED"],
                error_message="RATE_LIMIT_EXCEEDED",
            )
        except AuthenticationException as e:
            return Response(e.get_error_dict(), status=status.HTTP_429_TOO_MANY_REQUESTS)


class EmailVerificationThrottle(UserRateThrottle):
    """
    Throttle for email verification code generation.
    Limits to 3 requests per hour per user to prevent abuse.
    """

    scope = "email_verification"

    def __init__(self):
        # Get rate from instance configuration BEFORE calling super().__init__()
        (rate_limit,) = get_configuration_value(
            [
                {
                    "key": "RATE_LIMIT_EMAIL_VERIFICATION",
                    "default": os.environ.get("RATE_LIMIT_EMAIL_VERIFICATION", "3/hour"),
                }
            ]
        )
        self.rate = rate_limit or "3/hour"
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def throttle_failure_view(self, request, *args, **kwargs):
        try:
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["RATE_LIMIT_EXCEEDED"],
                error_message="RATE_LIMIT_EXCEEDED",
            )
        except AuthenticationException as e:
            return Response(e.get_error_dict(), status=status.HTTP_429_TOO_MANY_REQUESTS)
