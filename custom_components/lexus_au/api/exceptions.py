"""Exceptions raised by the Lexus Australia API client."""


class LexusAUError(Exception):
    """Base exception for Lexus Australia client failures."""


class LexusAUAuthError(LexusAUError):
    """Authentication or token management failed."""


class LexusAURequestError(LexusAUError):
    """The API returned an unexpected HTTP response."""


class LexusAUProtocolError(LexusAUError):
    """The server response did not match the captured protocol."""
