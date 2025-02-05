from __future__ import annotations

import datetime as dt
import json
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, Formatter, LogRecord
from typing import Any, ClassVar, Dict, Iterable, List, Optional, Tuple, Type, override

from constants import LOG_RECORD_BUILTIN_ATTRS, LOGGING_COLORS, LOGGING_LEVEL_COLOR_MAP
from exceptions import InvalidAttributeError, InvalidColorError
from utilities import StrictEmbedBuilder

__all__ = (
    "ColorizedFormatter",
    "JSONLFormatter",
    "DiscordEmbedLoggingFormatter",
)


class JSONLFormatter(Formatter):
    """
    A custom log formatter that converts log records into JSON lines format.
    This formatter creates a structured JSON object for each log record with customizable
    field mapping and ensures logs are formatted as valid JSON strings.

    Inherits from `logging.Formatter` to customize log record formatting into JSON format.
    """

    # Class-level variable to store the single instance of the formatter
    _instance: Optional[JSONLFormatter] = None

    # Store the last used constructor arguments (args, kwargs)
    _last_args: Optional[Tuple[Any, ...]] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> JSONLFormatter:
        """
        Ensures that only one instance of the formatter is created. If an instance already exists with
        the same arguments, the existing instance is returned. Otherwise, a new instance is created.

        :param args: Arguments passed to the constructor.
        :param kwargs: Keyword arguments passed to the constructor.
        :return: The singleton instance of JSONLFormatter.
        """
        # Check if the current arguments are different from the previously stored arguments
        if cls._last_args != (args, tuple(kwargs.items())):
            # If the arguments are different, create a new instance and update '_last_args'
            cls._instance = super(JSONLFormatter, cls).__new__(
                cls
            )  # Create a new instance of the class
            cls._last_args = (
                args,
                tuple(kwargs.items()),
            )  # Update the stored arguments with the current ones

        # Return the singleton instance (new or reused)
        return cls._instance  # type: ignore

    def __init__(self, *, fmt_dict: Optional[Dict[str, str]] = None) -> None:
        """
        Initializes the formatter with an optional field mapping dictionary. This constructor is only called
        once because of the Singleton pattern.

        :param fmt_dict: An optional dictionary where keys represent custom JSON field names,
                         and values are the corresponding attributes of the log record.
                         If not provided, defaults to an empty dictionary.
        """
        # Set 'fmt_dict' to the passed dictionary, or an empty dictionary if None
        super().__init__()
        self.fmt_dict: Dict[str, str] = fmt_dict if fmt_dict is not None else {}

    @classmethod
    def get_instance(cls) -> JSONLFormatter:
        """
        Returns the current instance of the JSONLFormatter.

        :return: The singleton instance of JSONLFormatter.
        :raises: ValueError if the instance has not been created yet.
        """
        # Check if the class variable '_instance' is None, indicating that the instance has not been created yet
        if cls._instance is None:
            # Raise an exception if the instance does not exist, prompting the user to initialize it first
            raise ValueError(
                "Instance has not been created yet. Please initialize it first."
            )

        # Return the existing instance of the class if it has already been created
        return cls._instance

    @override
    def format(self, record: LogRecord) -> str:
        """
        Formats the log record into a JSON string.

        This method prepares the log record as a dictionary with keys and values
        specified by `fmt_dict` and ensures it contains important information like
        the log message, timestamp, and any additional exception or stack info.

        :param record: The log record to format.
        :return: A JSON string representing the formatted log record.
        """
        # Prepare a dictionary with log information by passing the 'record' to the '_prepare_log_dict' method
        message: Dict[str, str] = self._prepare_log_dict(record)

        # Convert the 'message' dictionary to a JSON string, using the 'str' function to handle non-serializable objects
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: LogRecord) -> Dict[str, str]:
        """
        Prepares the log record as a dictionary with custom and default fields.

        This method populates the log dictionary with common fields (e.g., message, timestamp)
        and any additional fields such as exception info or stack trace, while also applying
        the field mappings defined in `fmt_dict`.

        :param record: The log record to format.
        :return: A dictionary representing the log record.
        """
        # Fields that are always included in the log message (e.g., message, timestamp)
        always_fields: Dict[str, str] = {
            "message": record.getMessage(),  # The message of the log record
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
            # Timestamp in ISO format
        }

        # If there is exception information, add it to the dictionary
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        # If there is stack info, add it to the dictionary
        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        # Map the custom field names from 'fmt_dict' to the actual log record's attribute values
        message: Dict[str, str] = {
            key: (
                msg_val
                if (msg_val := always_fields.pop(value, None)) is not None
                else getattr(record, value)
            )
            for key, value in self.fmt_dict.items()
        }

        # Check if the 'level' attribute is a string before stripping any ANSI color codes
        # This ensures that we only attempt to remove color codes from strings
        if isinstance(message.get("level"), str):
            message["level"] = message["level"]

        # Add any remaining always-included fields to the final log dictionary
        message.update(always_fields)

        # Create a dictionary of non-standard attributes (those not in 'LOG_RECORD_BUILTIN_ATTRS')
        for key, value in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = value

        return message


class ColorizedFormatter(Formatter):
    """
    A logging formatter that applies colors to specific log record attributes,
    and optionally applies colors to log levels (e.g., ERROR, WARNING).

    This formatter extends the default 'logging.Formatter' and allows you to
    define a color scheme for various log record attributes (e.g., `levelname`,
    `name`, `message`). Colors are applied using ANSI escape codes.
    """

    RESET_SEQ: ClassVar[str] = (
        "\033[0m"  # ANSI escape sequence to reset color formatting
    )
    _instance: Optional[ColorizedFormatter] = (
        None  # Singleton instance of the formatter
    )
    _last_args: Optional[Tuple[Any, ...]] = (
        None  # Store the last used constructor arguments (args, kwargs)
    )

    def __new__(cls, *args: Any, **kwargs: Any) -> ColorizedFormatter:
        """
        This method ensures that only one instance of the formatter is created,
        unless the arguments passed to the constructor are different from the previous one.

        If the constructor arguments are different from the last used ones, a new instance is created.

        :param args: Arguments passed to the constructor.
        :param kwargs: Keyword arguments passed to the constructor.
        :return: The singleton instance of ColorizedFormatter (or a new one if arguments differ).
        """
        # Check if the current arguments are different from the previously stored arguments
        if cls._last_args != (args, tuple(kwargs.items())):
            # If the arguments are different, create a new instance and update '_last_args'
            cls._instance = super(ColorizedFormatter, cls).__new__(
                cls
            )  # Create a new instance of the class
            cls._last_args = (
                args,
                tuple(kwargs.items()),
            )  # Update the stored arguments with the current ones

        # Return the singleton instance (new or reused)
        return cls._instance  # type: ignore

    def __init__(
        self,
        fmt: str,
        colors: Optional[Dict[str, str]] = None,
        color_map: Optional[Dict[str, str]] = None,
        level_color_map: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initializes the 'ColorizedFormatter' with a format string, a color dictionary,
        and a mapping of log record attributes to their respective colors.

        :param fmt: The logging format string that specifies the structure of the log message.
        :param colors: A dictionary mapping color names to ANSI escape sequences.
        :param color_map: A dictionary mapping log record attribute names to color names.
        :param level_color_map: A dictionary mapping logging levels (e.g., ERROR) to color names.

        :raise InvalidColorError: If a specified color in the color_map is not in the colors' dictionary.
        :raise InvalidAttributeError: If an attribute in the color_map is not present in the log record.
        """
        # Initialize the base Formatter class with the provided format string
        # Store the dictionary of color codes (ANSI escape sequences) for later use
        # Store the mapping of log record attributes to color names
        super().__init__(fmt)
        self.colors = colors or LOGGING_COLORS
        self.color_map = color_map or {}

        # Store the mapping of log record levels to color names
        self.level_color_map = level_color_map or LOGGING_LEVEL_COLOR_MAP

        # Validate that all colors in 'color_map' and 'level_color_map' exist in 'self.colors'
        for color_name in set(self.color_map.values()).union(
            self.level_color_map.values()
        ):
            if color_name not in self.colors:
                raise InvalidColorError(color_name, list(self.colors.keys()))

    @classmethod
    def get_instance(cls) -> ColorizedFormatter:
        """
        Returns the current instance of the ColorizedFormatter.

        :return: The singleton instance of ColorizedFormatter.
        :raises: ValueError if the instance has not been created yet.
        """
        # Check if the class variable '_instance' is None, indicating that the instance has not been created yet
        if cls._instance is None:
            # Raise an exception if the instance does not exist, prompting the user to initialize it first
            raise ValueError(
                "Instance has not been created yet. Please initialize it first."
            )

        # Return the existing instance of the class if it has already been created
        return cls._instance

    @override
    def format(self, record: LogRecord) -> str:
        """
        Formats the log record, applying colors to attributes based on the color map.
        """
        # Create a copy of the record to avoid modifying the original
        # record = copy.copy(record)

        # Retrieve all available attributes from the record, ignoring dunder methods
        record_attributes = [
            attr
            for attr in dir(record)
            if not (attr.startswith("__") and attr.endswith("__"))
        ]

        # Iterate through the color_map to colorize specified attributes
        for attr, color_name in self.color_map.items():
            if not hasattr(record, attr):
                raise InvalidAttributeError(attr, record_attributes)

            # Retrieve the original value of the attribute
            original_value = str(getattr(record, attr))

            # Apply the color formatting
            colored_value = f"{self.colors[color_name]}{original_value}{self.RESET_SEQ}"

            # Update the copy's attribute with the colored value
            setattr(record, attr, colored_value)

        # Apply colors to log levels if specified
        if record.levelname in self.level_color_map:
            level_color = self.colors[self.level_color_map[record.levelname]]
            record.levelname = f"{level_color}{record.levelname}{self.RESET_SEQ}"

        # Call the parent class's format method to generate the final formatted message
        return super().format(record)


class DiscordEmbedLoggingFormatter(Formatter):
    """
    A custom logging formatter that sends logs as Discord embeds, with each log level having
    a specific title and color. The timestamp of the log message is displayed in the footer,
    while additional metadata like level and logger name are shown as fields within the embed.

    The formatter uses the `logging.LogRecord`'s level to select a title and color for each
    log message, ensuring visually distinct log entries for different severities.
    """

    def __init__(
        self,
        title_mapping: Optional[Dict[int, str]] = None,
        color_mapping: Optional[Dict[int, int]] = None,
        additional_fields: Optional[Dict[str, str]] = None,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Initializes the embed formatter with specific title and color mappings for log levels.

        :param title_mapping: A dictionary that maps log levels (e.g., DEBUG, INFO, ERROR)
                                                   to specific titles (e.g., "Debugging", "Info", "Critical Error").
        :param color_mapping: A dictionary that maps log levels to specific embed colors
                                                  (in hexadecimal format). E.g., 0x3498db for blue.
        :param additional_fields: A dictionary of additional fields to include in the embed (e.g., "Process", "File").
        :param args: Additional arguments passed to the parent `logging.Formatter` class.
        :param kwargs: Additional keyword arguments passed to the parent `logging.Formatter` class.
        """
        super().__init__(*args, **kwargs)

        # Default title and color mappings if not provided
        self.title_mapping = title_mapping or {
            DEBUG: "Debugging",
            INFO: "Information",
            WARNING: "Warning",
            ERROR: "Error",
            CRITICAL: "Critical Error",
        }

        self.color_mapping = color_mapping or {
            DEBUG: 0x00AAFF,  # Blue for debugging
            INFO: 0x3498DB,  # Standard Blue
            WARNING: 0xFFFF00,  # Yellow for warning
            ERROR: 0xFF5733,  # Red for error
            CRITICAL: 0xFF0000,  # Dark Red for critical
        }

        # Default additional_fields to an empty dictionary if none are provided
        self.additional_fields = additional_fields or {}

        # Validate additional fields using the constant 'LOG_RECORD_BUILTIN_ATTRS'
        self._validate_additional_fields()

    def _validate_additional_fields(self) -> None:
        # Check each field in 'additional_fields' to ensure it is valid
        invalid_fields = [
            value
            for value in self.additional_fields.values()
            if value not in LOG_RECORD_BUILTIN_ATTRS
        ]

        if invalid_fields:
            raise ValueError(f"Invalid fields found: {', '.join(invalid_fields)}")

    @override
    def format(self, record: LogRecord) -> Dict[str, Any]:  # type: ignore
        """
        Formats the log record as a Discord embed with customized title, color, and footer.

        :param record: The log record to format.
        :return: A dictionary representing a Discord embed with the log content.
        """
        # Extract custom or default values for title, color, and timestamp
        title = self.title_mapping.get(record.levelno, "Log Message")
        color = self.color_mapping.get(record.levelno, 0x3498DB)  # Default to blue
        iso_timestamp = dt.datetime.fromtimestamp(record.created, dt.timezone.utc)

        # Create an embed message to represent the log details
        embed = StrictEmbedBuilder(
            title=title,  # Set the embed title to the log level (e.g., "ERROR", "INFO", etc.)
            description=f"```{super().format(record)}```",
            # Format the log message into a code block for better readability
            color=color,  # Assign the color of the embed based on the log level
            timestamp=iso_timestamp,  # Include the timestamp of the log event in the embed
        )

        # Add any additional custom fields defined in 'self.additional_fields'
        # These fields are added to the embed and will be displayed inline
        for field_name, field_value in self.additional_fields.items():
            # Extract the value for each custom field from the 'record', defaulting to 'N/A' if not found
            embed.add_field(
                name=field_name,  # Name of the custom field
                value=f"```{getattr(record, field_value, 'N/A')}```",  # Field value formatted in a code block
                inline=True,  # Fields are displayed inline for compactness
            )

        # Return the constructed embed object containing all the log details
        return embed.to_dict()  # type: ignore

    def format_batch(self, records: Iterable[LogRecord]) -> List[Dict[str, Any]]:
        """
        Formats a batch of log records as multiple embeds, each with its own title and color.

        :param records: A list of log records to format.
        :return: A dictionary representing a list of embeds for all the logs.
        """
        # Return a list of formatted log entries by iterating over each record in 'records'
        return [self.format(record) for record in records]
