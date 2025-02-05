from typing import Dict, Final, Set

from ._meta import ImmutableCollection

# Explicitly export specific names to be available in the module's namespace
# This helps in controlling which names are exposed when the module is imported
__all__ = (
    "LOGGING_COLORS",
    "LOGGING_LEVEL_COLOR_MAP",
    "LOG_RECORD_BUILTIN_ATTRS",
    "TIME_CONVERSION_CONSTANTS",
)


# Create another 'ImmutableCollection' instance for the time constants
TIME_CONVERSION_CONSTANTS: Final[ImmutableCollection[int]] = ImmutableCollection(
    seconds_in_minute=60,
    seconds_in_hour=3600,
    seconds_in_day=86400,
    seconds_in_week=604800,
    seconds_in_month=2592000,
    seconds_in_year=31536000,
)

# Define color codes for logging output using ANSI escape sequences
# These can be used to colorize log messages in the terminal
LOGGING_COLORS: Final[Dict[str, str]] = {
    "black": "\033[30m",  # Black color, typically used for dark backgrounds or subtle text
    "white": "\033[37m",  # White color, useful for light text or highlighting on dark backgrounds
    "red": "\033[31m",  # Red color for error or critical messages
    "green": "\033[32m",  # Green color for success or info messages
    "yellow": "\033[33m",  # Yellow color for warnings or alerts
    "blue": "\033[34m",  # Blue color for general informational messages
    "magenta": "\033[35m",  # Magenta color for debugging or special messages
    "cyan": "\033[36m",  # Cyan color for other informational messages
}

# Define a dictionary that maps logging levels to specific colors
LOGGING_LEVEL_COLOR_MAP: Final[Dict[str, str]] = {
    "DEBUG": "blue",
    "INFO": "cyan",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "magenta",
}

# Define the set of standard log record attributes that should be excluded from the custom message fields
LOG_RECORD_BUILTIN_ATTRS: Set[str] = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}
