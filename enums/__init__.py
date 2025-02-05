from enum import Enum, IntEnum, StrEnum
from logging import CRITICAL, DEBUG, ERROR, INFO, NOTSET, WARNING


# Define the LogSeverity enum for specifying log levels
class LogSeverity(IntEnum):
    """
    Enum representing standard logging levels for consistent severity control.
    Maps standard logging levels to enum members for use in configuration.

    :cvar NOTSET: Indication of unavailability.
    :cvar DEBUG: Detailed diagnostic information.
    :cvar INFO: Confirmation of normal operation.
    :cvar WARNING: Indication of potential issues.
    :cvar ERROR: Serious program errors.
    :cvar CRITICAL: Critical system failures.
    """

    NOTSET = NOTSET
    DEBUG = DEBUG
    INFO = INFO
    WARNING = WARNING
    ERROR = ERROR
    CRITICAL = CRITICAL
