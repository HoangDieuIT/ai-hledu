import time
from dataclasses import dataclass
from typing import Any, Optional, Dict, TYPE_CHECKING
from fastapi import Header
import pyotp
from app.model.errors import Errors

if TYPE_CHECKING:
    from app.resources import ResourceSession

from .errors import abort


class OTPAuthService:
    """
    OTP (One-Time Password) authentication service using TOTP (Time-based OTP).
    Generates 8-digit codes valid for 30 seconds.
    """

    def __init__(self, secret_key: str, period: int = 30, digits: int = 8, issuer: str = "Hledu API"):
        self.secret_key = secret_key
        self.period = period
        self.digits = digits
        self.issuer = issuer
        
        if len(self.secret_key) != 32:
            raise ValueError("OTP secret key must be exactly 32 characters")
        
        self.totp = pyotp.TOTP(
            s=self.secret_key,
            digits=self.digits,
            interval=self.period,
            issuer=self.issuer
        )

    def generate_token(self, timestamp: Optional[float] = None) -> str:
        """
        Generate current OTP token.
        """
        if timestamp:
            return self.totp.at(timestamp)
        return self.totp.now()

    def verify_token(self, token: str, timestamp: Optional[float] = None, window: int = 1) -> bool:
        """
        Verify OTP token with time window tolerance.
        """
        if not token or len(token) != self.digits:
            return False
        
        if timestamp:
            return self.totp.verify(token, for_time=timestamp, valid_window=window)
        return self.totp.verify(token, valid_window=window)

    def get_remaining_time(self, timestamp: Optional[float] = None) -> int:
        """
        Get remaining seconds until current OTP expires.
        """
        if timestamp is None:
            timestamp = time.time()
        return self.period - int(timestamp % self.period)

    def verify(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify token and return claims if valid.
        """
        if self.verify_token(token):
            return {
                'valid': True,
                'remaining_time': self.get_remaining_time(),
                'timestamp': time.time()
            }
        return None

    def get_provisioning_uri(self, account_name: str) -> str:
        """
        Get provisioning URI for QR code generation.
        """
        return self.totp.provisioning_uri(
            name=account_name,
            issuer_name=self.issuer
        )


@dataclass
class OTPAuthorized:
    """
    OTP authorization result containing validation claims.
    """
    claims: dict[str, Any]
    is_valid: bool


class OTPAuthorization:
    """
    OTP-based authorization handler - expects only 8-digit OTP code.
    """

    async def __call__(
        self,
        x_otp_token: str = Header(alias="X-OTP-Token", description="8-digit OTP token"),
    ) -> OTPAuthorized:
        if not x_otp_token:
            abort(401, code=Errors.UNAUTHORIZED.name, message="OTP token is required")
        
        if not x_otp_token.isdigit() or len(x_otp_token) != 8:
            abort(401, code=Errors.UNAUTHORIZED.name, message="OTP token must be 8 digits")

        from app.resources import context as r
        claims = r.auth.verify(x_otp_token)
        
        if not claims:
            abort(401, code=Errors.UNAUTHORIZED.name, message="Invalid or expired OTP token")

        return OTPAuthorized(claims=claims, is_valid=True)


class OptionalOTPAuthorization:
    """
    Optional OTP authorization for endpoints that can work with or without auth.
    """

    async def __call__(
        self,
        x_otp_token: Optional[str] = Header(default=None, alias="X-OTP-Token"),
    ) -> OTPAuthorized:
        if not x_otp_token:
            return OTPAuthorized(claims={}, is_valid=False)

        if not x_otp_token.isdigit() or len(x_otp_token) != 8:
            return OTPAuthorized(claims={}, is_valid=False)

        from app.resources import context as r
        claims = r.auth.verify(x_otp_token)
        
        return OTPAuthorized(
            claims=claims or {},
            is_valid=claims is not None
        )


#----------------------------------------------------------------
# Dependencies
#----------------------------------------------------------------
with_otp = OTPAuthorization()
maybe_otp = OptionalOTPAuthorization()