import sys

# Disable the creation of '__pycache__' directories by the Python interpreter
# Normally, Python generates '.pyc' files in a '__pycache__' directory when a module is imported
# These '.pyc' files contain the bytecode compiled from the Python source code, which helps speed up subsequent imports
# By setting 'sys.dont_write_bytecode' to 'True', this behavior is suppressed
# This can be useful in scenarios where you want to avoid clutter, reduce disk writes, or ensure
# that only source files are used (e.g., in environments with strict file management policies)
sys.dont_write_bytecode = True

import asyncio
import logging
import platform

from structures import EnvVariables, SanitizedWrapper

# Import utility functions for loading environment variables, logging configuration and other things
from utilities.functions import load_env_variables, load_logging_config

# Get a logger instance for the current module (file) to log messages
logger = logging.getLogger(__name__)

# Load 'WEBHOOK_TOKEN', 'WEBHOOK_ID', 'BOT_TOKEN' and 'APPLICATION_ID' from the '.env' file into the 'credentials' variable
# Apply sanitization to convert placeholder values like empty strings, "NULL", and "None" (as strings)
# Into actual None values, ensuring that they're valid
credentials: EnvVariables = SanitizedWrapper(
    EnvVariables(
        **load_env_variables(
            env_file=".env",
            variable_names=(
                "LOGGING_WEBHOOK_TOKEN",
                "LOGGING_WEBHOOK_ID",
                "BOT_TOKEN",
                "APPLICATION_ID",
            ),
        )
    )
)
# Load the logging configuration from the default 'logging_config.json' file
logging_configuration = load_logging_config("logging_config.json")

# Replace placeholders in the logging configuration with actual values from the environment
for handler in logging_configuration["handlers"].values():
    if handler.get("class") == "logging_.handlers.DiscordWebHookHandler":
        handler["webhook_token"] = (
            credentials.logging_webhook_token
        )  # Set the actual webhook token
        handler["webhook_id"] = (
            credentials.logging_webhook_id
        )  # Set the actual webhook ID

# Import logging configuration functionality
import logging.config

# Apply the loaded logging configuration to the logging system
logging.config.dictConfig(config=logging_configuration)

# Check if Python is running with optimization flags (-O or -OO)
# If the '-OO' flag is passed, the '__debug__' variable will be False
# In such cases, the program will log an info message and exit
if not __debug__:
    logger.info("This program cannot be run with the -O or -OO flags.")
    sys.exit(1)


def validate_credentials() -> None:
    """
    Validates the environment variables loaded into the 'credentials' global variable.
    Logs a warning if any required environment variables are None.
    """
    # An instance of the 'EnvVariables' class containing the environment variables
    global credentials

    if not credentials.is_valid():
        # Get the keys where the values are None
        invalid_keys = [
            key for key, value in credentials.to_dict().items() if value is None
        ]

        # Log a warning about missing environment variables
        if invalid_keys:
            logger.warning(
                f"The following environment variables are missing or invalid: {', '.join(invalid_keys)}. "
                "This may cause certain functionalities to break or the bot to not work properly!"
            )


# Set up the asyncio event loop policy and check for platform-specific conditions
def configure_event_loop() -> None:
    """
    Configures the asyncio event loop based on the operating system.
    Uses uvloop on UNIX-based systems for better performance if available.
    For Windows, performs additional checks to determine compatibility and settings.
    """
    system_name = platform.system()
    logger.info(f"Detected OS: {system_name}.")

    if system_name == "Windows":
        _configure_windows_event_loop()
    elif system_name in ("Linux", "Darwin"):  # For Linux and macOS
        _configure_unix_event_loop()
    else:
        logger.info(
            "Unrecognized or unsupported platform detected. "
            "Using the default asyncio event loop."
        )
        _log_current_policy()


def _configure_windows_event_loop() -> None:
    """
    Configures the event loop for Windows systems.
    Checks Python version compatibility and logs warnings for potential limitations.
    """
    required_python = (3, 13)
    current_version = sys.version_info

    if current_version < required_python:
        required_str = ".".join(map(str, required_python))
        current_str = ".".join(map(str, current_version[:3]))
        logger.warning(
            f"Python {current_str} detected - Asyncio on Windows works best with Python {required_str}+. "
            "Some features like asyncio.to_thread() may not be available."
        )

    # Check if running on Windows Subsystem for Linux (WSL)
    if "microsoft" in platform.uname().release.lower():
        logger.info(
            "Running on Windows Subsystem for Linux (WSL). "
            "Uvloop may be an option if the Linux subsystem supports it."
        )

    logger.info("Using the default asyncio event loop for Windows.")
    _log_current_policy()


def _configure_unix_event_loop() -> None:
    """
    Configures the event loop for UNIX-based systems (Linux and macOS).
    Attempts to use uvloop for better performance if available.
    Falls back to the default asyncio event loop if uvloop is not installed or encounters errors.
    """
    try:
        import uvloop

        uvloop.install()
        logger.info("Successfully installed uvloop for enhanced performance.")
        _log_current_policy()
    except (ImportError, ModuleNotFoundError, AttributeError) as error:
        logger.error(
            f"Error while importing uvloop: {str(error)}\n"
            "uvloop is not installed or not configured properly. Using the default asyncio event loop."
        )
        _log_current_policy()
    except Exception as error:
        logger.error(
            f"An unexpected error occurred while configuring uvloop: {error}\n"
            "Falling back to the default asyncio event loop."
        )
        _log_current_policy()


def _log_current_policy(message: str = None) -> None:
    """
    Logs the current event loop policy for debugging and diagnostics.
    Optionally includes a custom message to provide context.
    """
    if message:
        logger.info(message)

    try:
        policy = asyncio.get_event_loop_policy()
        policy_info = f"{policy.__class__.__module__}.{policy.__class__.__name__}"
        logger.debug(f"Active event loop policy: {policy_info}")
    except Exception as error:
        logger.warning(f"Could not determine event loop policy: {str(error)}")


async def main() -> None:
    """
    The main coroutine that initializes and starts the Discord bot.
    It doesn't accept any parameters and runs the bot with the default configuration unless overridden.
    """
    ...


# Ensure the script only runs when executed directly
if __name__ == "__main__":
    # Validate the credentials and log a warning if any environment variables are missing or invalid
    validate_credentials()

    # Apply the event loop configuration
    configure_event_loop()

    # Run the main asyncio event loop
    asyncio.run(main())
