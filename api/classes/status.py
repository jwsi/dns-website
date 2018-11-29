from enum import IntEnum

class ReturnCode(IntEnum):
    """
    Enumeration to define return codes for requests.
    """
    # Global success code
    SUCCESS = 0
    # Checking Errors
    DOMAIN_NOT_FOUND = 100
    CHECK_FAILED = 101
    DOMAIN_ALREADY_LIVE = 102